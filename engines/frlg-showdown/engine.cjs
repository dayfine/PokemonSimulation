/** FireRed/LeafGreen (Gen 3) adapter for Pokemon Showdown. Bag items are queued events, never fake moves. */
'use strict';
const {Battle, Dex, toID} = require('pokemon-showdown');
const {movePreview} = require('./damage.cjs');
const GEN = Dex.mod('gen3');
const HEALS = {potion: 20, superpotion: 50, hyperpotion: 200, maxpotion: Infinity, fullrestore: Infinity};
const CURES = {awakening: ['slp'], antidote: ['psn', 'tox'], parlyzheal: ['par'],
  burnheal: ['brn'], iceheal: ['frz'], fullheal: ['slp', 'psn', 'tox', 'par', 'brn', 'frz'],
  fullrestore: ['slp', 'psn', 'tox', 'par', 'brn', 'frz']};

function applyBag(battle, pokemon, item) {
  if (!(pokemon.side.pokesimBag[item] > 0)) throw new Error(`No ${item} left`);
  pokemon.side.pokesimBag[item]--;
  battle.add('message', `${pokemon.side.name} used ${item}`);
  if (HEALS[item]) battle.heal(HEALS[item] === Infinity ? pokemon.maxhp : HEALS[item], pokemon);
  if ((CURES[item] || []).includes(pokemon.status)) pokemon.cureStatus();
  if (['fullheal', 'fullrestore'].includes(item)) pokemon.removeVolatile('confusion');
  pokemon.side.pokesimUsed[item] = (pokemon.side.pokesimUsed[item] || 0) + 1;
}

function teamMember(input) {
  const species = GEN.species.get(toID(input.species));
  if (!species.exists || species.gen > 3) throw new Error(`Unknown Gen 3 species ${input.species}`);
  const moves = input.moves.map(move => typeof move === 'string' ? move : move.name);
  for (const name of moves) {
    const move = GEN.moves.get(toID(name));
    if (!move.exists || move.gen > 3) throw new Error(`Unknown Gen 3 move ${name}`);
  }
  const ivs = input.ivs || Object.fromEntries(['hp', 'atk', 'def', 'spa', 'spd', 'spe'].map(s => [s, input.iv ?? 15]));
  return {species: species.name, name: species.name, level: input.level,
    nature: input.nature || 'Hardy', ability: input.ability || species.abilities[input.ability_slot || 0],
    gender: input.gender || (species.gender || 'M'), item: input.held_item || '',
    ivs, evs: input.evs || {hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0}, moves};
}

function initialize(pokemon, input, badges = []) {
  const stats = input.stats || {hp: pokemon.maxhp, ...pokemon.storedStats};
  pokemon.maxhp = pokemon.baseMaxhp = stats.hp;
  pokemon.hp = input.hp ?? stats.hp;
  pokemon.baseStoredStats = {...stats};
  for (const stat of ['atk', 'def', 'spa', 'spd', 'spe']) pokemon.storedStats[stat] = stats[stat];
  // FRLG badges boost the raw stat before stat stages (pokemon.c).
  const badgeStats = {boulder: ['atk'], soul: ['def'], volcano: ['spa', 'spd'], thunder: ['spe']};
  for (const badge of badges) {
    if (!['boulder', 'cascade', 'thunder', 'rainbow', 'soul', 'marsh', 'volcano', 'earth'].includes(badge)) {
      throw new Error(`Unknown FRLG badge ${badge}`);
    }
    for (const stat of badgeStats[badge] || []) pokemon.storedStats[stat] = Math.floor(stats[stat] * 110 / 100);
  }
  pokemon.speed = pokemon.getStat('spe');
  for (let i = 0; i < pokemon.moveSlots.length; i++) {
    const slot = pokemon.moveSlots[i];
    const move = GEN.moves.get(slot.id);
    const supplied = input.moves[i];
    slot.maxpp = move.pp; // Showdown defaults to PP Ups; story fixtures do not.
    slot.pp = typeof supplied === 'object' ? supplied.pp : move.pp;
  }
  if (input.status) pokemon.setStatus(input.status);
  if (input.sleep_turns !== undefined) pokemon.statusState.time = input.sleep_turns;
  if (input.boosts) pokemon.setBoost(input.boosts);
}

function createBattle(scenario, seed) {
  const format = new Dex.Format({
    name: 'Pokesim FRLG', mod: 'gen3', gameType: 'singles', ruleset: [],
    // Bag priority 6 is above moves. Running an event bypasses BeforeMove:
    // no sleep countdown, confusion roll, paralysis roll, or move PP cost.
    onPokesimBag(pokemon) { applyBag(this, pokemon, pokemon.side.pokesimPending); },
    onFaint(pokemon, source, effect) {
      // Showdown clears volatiles immediately after Faint. Preserve evidence
      // before cleanup, without changing the battle or drawing randomness.
      pokemon.pokesimFaint = {status: pokemon.status,
        volatiles: Object.keys(pokemon.volatiles), boosts: {...pokemon.boosts},
        source: source?.species.id || null, effect: effect?.id || null};
    },
    onBattleStart() {
      for (const side of [this.p1, this.p2]) {
        const inputs = side === this.p1 ? [scenario.player] : scenario.trainer.party;
        const bag = side === this.p1 ? scenario.bag : scenario.trainer.bag;
        side.pokesimBag = Object.fromEntries(Object.entries(bag || {}).map(([k, v]) => [toID(k), v]));
        side.pokesimUsed = {};
        for (let i = 0; i < side.pokemon.length; i++) {
          initialize(side.pokemon[i], inputs[i], side === this.p1 ? scenario.badges : []);
          side.pokemon[i].pokesimPartyIndex = i;
        }
      }
    },
  });
  const battle = new Battle({format, seed, strictChoices: true,
    p1: {name: 'Player', team: [teamMember(scenario.player)]},
    p2: {name: 'Trainer', team: scenario.trainer.party.map(teamMember)},
  });
  battle.pokesimScenario = scenario;
  return battle;
}

function choose(battle, side, action) {
  if (!action) throw new Error(`Missing action for ${side.id}`);
  if (action.kind === 'item') {
    const item = toID(action.item);
    if (!HEALS[item] && !CURES[item]) throw new Error(`Unsupported bag item ${item}`);
    if (!(side.pokesimBag[item] > 0)) throw new Error(`No ${item} left`);
    if (side.active[0].getLockedMove()) throw new Error('A two-turn move cannot be interrupted by a bag item');
    side.choose('default');
    side.pokesimPending = item;
    side.choice.actions = [{choice: 'event', pokemon: side.active[0], event: 'PokesimBag', priority: 6}];
  } else if (action.kind === 'move') {
    side.choose(`move ${action.slot + 1}`);
  } else if (action.kind === 'switch') {
    side.choose(`switch ${action.slot + 1}`);
  } else if (action.kind === 'pass') {
    if (!side.isChoiceDone()) side.choose('pass');
  } else throw new Error(`Unknown action ${action.kind}`);
}

function playTurn(battle, own, foe) {
  // Populate both sides before committing, so neither acts before its bag
  // event has replaced the chosen action. Node modules are never patched.
  choose(battle, battle.p1, own);
  choose(battle, battle.p2, foe);
  battle.commitChoices();
}

function monState(pokemon, target, previews = true) {
  const state = {species: pokemon.species.id, hp: pokemon.hp, max_hp: pokemon.maxhp,
    level: pokemon.level, stats: {...pokemon.storedStats}, speed: pokemon.getStat('spe'),
    faint: pokemon.pokesimFaint || null,
    status: pokemon.status, sleep_turns: pokemon.statusState.time || 0,
    boosts: {...pokemon.boosts}, types: pokemon.getTypes(), ability: pokemon.ability,
    volatiles: Object.keys(pokemon.volatiles), last_move: pokemon.lastMove?.id || '',
    locked_move: pokemon.getLockedMove() || '', position: pokemon.position, party_index: pokemon.pokesimPartyIndex,
    moves: pokemon.moveSlots.map(s => ({id: s.id, pp: s.pp, disabled: !!s.disabled}))};
  if (previews && target?.hp && pokemon.hp) {
    state.moves = pokemon.moveSlots.map(slot => movePreview(pokemon, target, slot));
  }
  if (target) {
    const types = target.getTypes();
    state.replacement_type_score = [types[0], types[1] || types[0]].reduce((score, type) =>
      score * (pokemon.battle.dex.getImmunity(type, pokemon) ?
        2 ** pokemon.battle.dex.getEffectiveness(type, pokemon) : 0), 1);
  }
  return state;
}

function snapshot(battle, traceFrom = 0) {
  const own = battle.p1.active[0];
  const foe = battle.p2.active[0];
  const needsSwitch = !!battle.p2.activeRequest?.forceSwitch;
  return {turn: battle.turn, ended: battle.ended, winner: battle.winner || null,
    request: battle.requestState, needs_switch: needsSwitch,
    own: monState(own, foe, !needsSwitch), foe: monState(foe, own),
    party: battle.p2.pokemon.map(p => monState(p, own, needsSwitch)),
    bag: {...battle.p1.pokesimBag}, trainer_bag: {...battle.p2.pokesimBag},
    items_used: {...battle.p1.pokesimUsed}, trainer_items_used: {...battle.p2.pokesimUsed},
    log: battle.log.slice(traceFrom).filter(line => !line.startsWith('|t:|'))};
}
module.exports = {createBattle, playTurn, snapshot, applyBag, initialize, teamMember};
