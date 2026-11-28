const {Battle, Dex, toID} = require(process.env.SHOWDOWN_MODULE || 'pokemon-showdown');
const fixtures = require('./bdsp-speedrun-fixtures.json');
const policy = process.env.BDSP_POLICY || 'C';
if (!['A', 'B', 'C'].includes(policy)) throw Error('BDSP_POLICY must be A, B or C');

const dex = Dex.mod('gen8bdsp');
const statNames = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
const kazzaIvs = [28, 10, 9, 11, 3, 31];
const toStats = values => Object.fromEntries(statNames.map((stat, i) => [stat, values[i]]));

const items = {
  xdef: {boost: {def: 2}}, xspd: {boost: {spe: 2}},
  xspa: {boost: {spa: 2}}, xspdef: {boost: {spd: 2}}, xacc: {boost: {accuracy: 2}},
  pot: {heal: 20}, super: {heal: 60}, root: {heal: 120},
  full: {heal: Infinity, cure: true}, revival: {revive: true},
};

// Sequences are per active opponent. Once the sequence is exhausted, select an attack.
const plans = {
  '1': {starly: ['leer', 'scratch']},
  '3': {bidoof: ['ember', 'scratch']},
  '178': {starly: ['ember'], piplup: ['pot', 'ember']},
  '174': {geodude: ['focusenergy', 'lowkick'], onix: ['lowkick']},
  '175': {geodude: ['xdef', 'revenge'], onix: ['lowkick'], cranidos: ['revenge']},
  '221': {wurmple: ['taunt', 'ember']},
  '220': {zubat: ['taunt', 'ember'], purugly: ['pot', 'poweruppunch', 'poweruppunch', 'machpunch']},
  '153': {pachirisu: ['poweruppunch', 'machpunch', 'ember']},
  '183': {'budew:2': ['taunt', 'ember']},
  '240': {cherubi: ['poweruppunch', 'flamewheel'], turtwig: ['flamewheel'], roserade: ['flamewheel']},
  '311': {zubat: ['confusion'], skuntank: ['switch:m', 'poweruppunch', 'poweruppunch', 'flamewheel', 'super', 'flamewheel']},
  '229': {bronzor: ['poweruppunch', 'poweruppunch', 'machpunch'], shieldon: ['machpunch', 'flamewheel']},
  '211': {glameow: ['confusion'], kadabra: ['grassknot', 'grassknot', 'shockwave']},
  '202': {monferno: ['confusion'], gyarados: ['shockwave']},
  '242': {meditite: ['xdef', 'xspa', 'xspa', 'xacc', 'xspd', 'confusion'], machoke: ['psychic'], lucario: ['psychic']},
  '374': {azurill: ['confusion'], marill: ['psychic']},
  '241': {gyarados: ['shockwave'], quagsire: ['switchfree:m', 'taunt', 'xspd', 'grassknot'], floatzel: ['grassknot']},
  '356': {starly: ['xspa', 'shockwave'], prinplup: ['psyshock'], roselia: ['psyshock'], ponyta: ['shockwave']},
  '243': {drifblim: ['xspdef', 'xspd', 'super', 'super', 'xspa', 'psyshock'], gengar: ['psychic'], mismagius: ['psyshock']},
  '359': {staravia: ['shockwave'], heracross: ['psychic'], roselia: ['psychic'], ponyta: ['psychic'], prinplup: ['psychic']},
  '179': {bronzor: ['taunt', 'stealthrock', 'flamethrower', 'taunt', 'machpunch', 'flamethrower'], steelix: ['taunt', 'grassknot'], bastiodon: ['xspa', 'grassknot']},
  '313': {kadabra: ['shadowball'], toxicroak: ['psyshock'], bronzor: ['shadowball']},
  '314': {kadabra: ['shadowball'], toxicroak: ['psyshock'], bronzor: ['shadowball']},
  '310': {golbat: ['psychic'], purugly: ['psychic'], bronzor: ['shadowball']},
  '244': {snover: ['xspa', 'dazzlinggleam'], sneasel: ['dazzlinggleam'], medicham: ['psychic'], abomasnow: ['psychic']},
  '382': {dustox: ['psychic'], bronzor: ['shadowball']},
  '308': {murkrow: ['dazzlinggleam'], golbat: ['psyshock'], sneasel: ['dazzlinggleam']},
  '398': {bronzor: ['shadowball'], glameow: ['psyshock']},
  '393': {bronzor: ['shadowball'], golbat: ['psyshock']},
  '399': {golbat: ['psyshock'], glameow: ['psyshock'], bronzor: ['shadowball']},
  '309': {honchkrow: ['dazzlinggleam'], gyarados: ['psyshock', 'revival:m', 'psychic'], crobat: ['psychic'], weavile: ['xspa', 'dazzlinggleam']},
  '245': {raichu: ['xspa', 'surf'], ambipom: ['xspd', 'surf'], octillery: ['surf'], luxray: ['surf']},
  '160': {tentacruel: ['psychic'], golem: ['psychic'], empoleon: ['psychic', 'surf']},
  '362': {staraptor: ['xspd', 'xspa', 'surf'], rapidash: ['xspa', 'surf']},
  '185': {dustox: ['xspd', 'xspa', 'xspa', 'full', 'surf']},
  '186': {quagsire: ['xdef', 'xspa', 'full', 'dragonpulse'], golem: ['slash', 'dragonpulse']},
  '187': {rapidash: ['xspd', 'xdef', 'xspa', 'surf']},
  '188': {mrmime: ['xspdef', 'xspd', 'xspa', 'xspa', 'xspa', 'surf']},
  '191': {spiritomb: ['xspdef', 'xspd', 'xspa', 'xspa', 'dragonpulse']},
};
const repeatedAttacks = {'362':'surf', '185':'surf', '186':'dragonpulse', '187':'surf', '188':'surf', '191':'dragonpulse'};
const doublesPlans = {
  '318+317': {c: [['ember','wurmple'], ['ember','zubat']]},
  '154+155': {m: [['poweruppunch','abra']]},
  '315+324': {k: [['confusion','wurmple'], ['confusion','cascoon']], m: [['flamewheel','zubat'], ['flamewheel','glameow']]},
  '674+675': {m: [['flamethrower','beautifly'], ['flamethrower','stunky'], ['flamethrower','dustox'], ['flamethrower','croagunk']]},
  '322+328': {k: [['dazzlinggleam']], m: [['xspa'], ['xspa'], ['root']]},
  '387+662': {k: [['dazzlinggleam']], m: [['flamethrower']]},
  '400+394': {k: [['dazzlinggleam']], m: [['flamethrower','dustox']]},
  '401+312': {k: [['xdef'], ['xspa'], ['shadowball','bronzor'], ['psychic','golbat'], ['root'], ['psychic','purugly'], ['dazzlinggleam'], ['psychic','golbat']]},
};
const faintLevels = {
  '178': {starly: 'c'}, '174': {geodude: 'f'}, '175': {geodude: 'f', onix: 'f'},
  '240': {turtwig:'m'}, '353': {roselia:'km'}, '356': {prinplup:'k'},
  '243': {gengar:'k'}, '359': {roselia:'k'}, '179': {steelix:'k'},
  '313': {kadabra:'k'}, '309': {crobat:'k'}, '245': {raichu:'p'}, '156': {rapidash:'k'},
  '362': {rapidash:'p'}, '188': {girafarig:'p'}, '191': {gastrodon:'p'},
};
// Scenario 0 replays these choices when legal and resolves damage with a fresh RNG seed.
const npcOpenings = {
  '1': {starly: ['quickattack','tackle','quickattack','tackle']},
  '2': {shinx: ['leer']},
  '3': {bidoof: ['tackle']},
  '178': {starly: ['tackle','quickattack'], piplup: ['growl','growl','pound','pound','growl']},
  '174': {geodude: ['tackle','tackle','tackle'], onix: ['harden','harden']},
  '175': {geodude: ['rollout','stealthrock','rollout'], onix: ['rockthrow','rockthrow'], cranidos: ['headbutt']},
  '220': {zubat: ['supersonic','astonish','astonish'], purugly: ['scratch','scratch','scratch']},
  '240': {cherubi: ['dazzlinggleam'], roserade: ['grassknot']},
  '311': {skuntank: ['poisongas','poisongas','acidspray','flamethrower','snarl']},
  '242': {meditite: ['flash','lightscreen','bulkup','drainpunch','drainpunch']},
  '241': {quagsire: ['mudshot','mudshot']},
  '356': {starly: ['pluck']},
  '243': {drifblim: ['hex','fly','fly','fly','fly']},
  '239': {steelix: ['irontail']},
  '179': {bronzor: ['trickroom','flashcannon','flashcannon','trickroom','flashcannon'], steelix: ['earthquake'], bastiodon: ['stoneedge']},
  '244': {snover: ['avalanche']},
  '309': {gyarados: ['crunch','waterfall'], crobat: ['tailwind'], weavile: ['dig','dig']},
  '245': {raichu: ['voltswitch'], ambipom: ['fakeout']},
  '362': {staraptor: ['raindance','uturn','uturn'], rapidash: ['megahorn']},
  '185': {dustox: ['lightscreen','bugbuzz','toxic','bugbuzz']},
  '186': {quagsire: ['earthquake','toxic','earthquake'], golem: ['rockpolish','earthquake']},
  '187': {rapidash: ['hypnosis','flamecharge','poisonjab','poisonjab','poisonjab'], infernape: ['closecombat']},
  '188': {mrmime: ['lightscreen','dazzlinggleam','reflect','dazzlinggleam','dazzlinggleam']},
  '191': {spiritomb: ['shadowball','suckerpunch','suckerpunch','suckerpunch']},
};
const observedPP = {
  'starly': {scratch: 35, leer: 30}, '1': {scratch: 35, leer: 30},
  '3': {scratch:32, leer:29, ember:25}, '2': {scratch:30, leer:29, ember:23},
  '178': {scratch:30, leer:29, ember:21}, '185': {surf:15},
};
const leaderMedicines = {
  '175': ['pot', 2], '240': ['super', 2], '242': ['super', 2], '241': ['super', 2],
  '243': ['super', 2], '179': ['super', 2], '244': ['super', 2], '245': ['full', 2],
  '185': ['full', 2], '186': ['full', 2], '187': ['full', 2], '188': ['full', 2], '191': ['full', 4],
};

function makeSet(mon, isPlayer) {
  const defaultIvs = mon.code === 'k' ? kazzaIvs : mon.code === 'p' ? [31, 20, 20, 31, 20, 31] :
    ['c','m'].includes(mon.code) ? [20, 15, 15, 15, 15, 25] : [15, 15, 15, 15, 15, 15];
  return {
    species: mon.species, name: mon.species, level: mon.level,
    item: mon.item || '', ability: mon.ability || dex.species.get(mon.species).abilities[0],
    moves: mon.moves, nature: mon.nature || (mon.code === 'k' ? 'Quiet' : 'Hardy'),
    evs: toStats(mon.evs || [0,0,0,0,0,0]), ivs: toStats(mon.ivs || defaultIvs),
    ...(isPlayer ? {gender: mon.code === 'f' ? 'F' : mon.code === 'p' ? 'N' : 'M'} : {}),
  };
}

function setEntry(pokemon, entry, key, scenario) {
  const [current, max] = entry.hp.split('/');
  const inferredMax = pokemon.maxhp;
  if (max && max !== '?') pokemon.maxhp = pokemon.baseMaxhp = +max;
  pokemon.hp = current === '?'
    ? Math.max(1, Math.floor(pokemon.maxhp * (scenario ? 0.75 : 1)))
    : Math.min(pokemon.maxhp, +current);
  for (const slot of pokemon.moveSlots) {
    // A cartridge move starts with base PP unless an item increased it.
    slot.maxpp = dex.moves.get(slot.id).pp;
    slot.pp = Math.min(slot.maxpp, observedPP[key]?.[slot.id] ?? slot.maxpp);
  }
  return pokemon.maxhp - inferredMax;
}

function policyAllows(item) {
  return policy === 'C' || (policy === 'B' && (items[item]?.heal || items[item]?.revive));
}

function bagAction(battle, target, item) {
  const {boost, heal, cure, revive} = items[item];
  if (revive && target.fainted) {
    target.fainted = false;
    target.faintQueued = false;
    target.side.pokemonLeft++;
    target.hp = target.maxhp;
    target.setStatus('');
  }
  if (boost) battle.boost(boost, target, target, {id: 'bag', name: 'X item', effectType: 'Item'});
  if (heal) {
    if (cure) target.cureStatus();
    target.sethp(Math.min(target.maxhp, target.hp + heal));
  }
}

function available(battle, actor, request) {
  const options = [];
  for (let index = 0; index < request.moves.length; index++) {
    const slot = request.moves[index];
    if (slot.disabled || slot.pp === 0) continue;
    const move = battle.dex.moves.get(slot.id);
    const targets = actor.side.foe.active.filter(p => p?.hp);
    const explicitTarget = ['normal','adjacentFoe','any'].includes(slot.target);
    for (const target of (explicitTarget ? targets : targets.slice(0,1))) {
      const loc = battle.activePerHalf > 1 && explicitTarget ? ' ' + actor.getLocOf(target) : '';
      options.push({id: slot.id, move, target, choice: 'move ' + (index + 1) + loc});
    }
  }
  return options.length ? options : [{id:'struggle', move:battle.dex.moves.get('struggle'), target:actor.side.foe.active.find(p=>p?.hp), choice:'move 1'}];
}

function attackScore(battle, actor, option) {
  const {move, target} = option;
  if (!target || move.category === 'Status') return 0;
  // getDamage consumes RNG and can add messages. Give scoring an independent, reset seed.
  const realRng = battle.prng;
  const realLog = battle.log;
  battle.prng = new realRng.constructor([13, 7, 11, 19]);
  battle.log = [];
  let damage;
  try {
    const activeMove = battle.dex.getActiveMove(move);
    if (move.id === "beatup") activeMove.allies = actor.side.pokemon.filter(mon => mon.hp && !mon.status);
    damage = battle.actions.getDamage(actor, target, activeMove, true);
  } finally {
    battle.prng = realRng;
    battle.log = realLog;
  }
  if (typeof damage !== 'number') return 0;
  const accuracy = move.accuracy === true ? 1 : move.accuracy / 100;
  const first = move.priority > 0 || actor.getStat('spe') >= target.getStat('spe');
  return accuracy * (Math.min(damage, target.hp * 1.1) + (damage >= target.hp && first ? target.hp * 0.25 : 0));
}

function chooseNpc(battle, actor, options, scenario, tactical) {
  if (!scenario && !tactical) return options[battle.random(options.length)];
  const scored = options.map(option => {
    const {move, target} = option;
    let score = attackScore(battle, actor, option);
    const utility = {
      lightscreen: 'lightscreen', reflect: 'reflect', trickroom:'trickroom',
      stealthrock: 'stealthrock', toxic: 'tox', hypnosis: 'slp', willowisp:'brn',
      flash:'accuracy', bulkup:'atk', rockpolish:'spe', raindance:'raindance',
    };
    const utilityTarget = utility[move.id];
    if (move.category === 'Status') {
      const unneeded = actor.side.sideConditions[utilityTarget] || target?.side.sideConditions[utilityTarget] ||
        battle.field.pseudoWeather[utilityTarget] || battle.field.weather === utilityTarget ||
        target?.status === utilityTarget || actor.boosts[utilityTarget] > 0 || target?.boosts[utilityTarget] < 0;
      const firstTurn = actor.activeTurns <= 1;
      score = target && utilityTarget && !unneeded
        ? target.maxhp * (firstTurn ? 0.45 : 0.18) * (scenario ? 0.65 : 1)
        : 0;
    }
    return {option, score: score + (target?.maxhp ?? 1) * battle.random(100) / (scenario ? 1200 : 300)};
  });
  return scored.reduce((best, next) => next.score > best.score ? next : best).option;
}

function playerChoice(battle, entry, actor, options, steps, pending, actorCode, rivalRecovery) {
  const foe = options.find(o => o.target)?.target;
  if (!foe) return options[0].choice;
  if (rivalRecovery && rivalRecovery.potions > 0 && actor.hp <= 11) {
    rivalRecovery.potions--;
    pending.set(actor, {item:'pot', target:actor});
    return options[0].choice;
  }
  const doublePlan = doublesPlans[entry.key]?.[actorCode];
  if (doublePlan) {
    const step = steps.get(actorCode) ?? 0;
    const [move, species] = doublePlan[Math.min(step, doublePlan.length - 1)];
    steps.set(actorCode, step + 1);
    if (items[move] && policyAllows(move) && step < doublePlan.length) {
      pending.set(actor, {item:move, target:actor.side.active[0]});
      return options[0].choice;
    }
    const plannedOption = options.find(o => o.id === move && (!species || o.target?.species.id === species));
    if (plannedOption) return plannedOption.choice;
  }
  const slot = foe.auditSlot;
  const species = foe.species.id.replace(/east$/, '');
  const plan = rivalRecovery ? ['ember'] : plans[entry.key]?.[species + ':' + slot] ?? plans[entry.key]?.[species];
  const counterKey = 'p1:' + slot;
  const step = steps.get(counterKey) ?? 0;
  const defaultMove = repeatedAttacks[entry.key] || entry.attack;
  const planned = plan?.[Math.min(step, plan.length - 1)] ?? defaultMove;

  if (actorCode === 'ally') return chooseNpc(battle, actor, options, 1, false).choice;
  if (plan && step < plan.length) steps.set(counterKey, step + 1);

  if (policy === 'C' && planned?.startsWith('switch')) {
    const [, code] = planned.split(':');
    const target = actor.side.pokemon.find(p => p.auditCode === code && p.hp && !p.isActive);
    if (target) {
      return 'switch ' + (target.position + 1);
    }
  }

  const [item, code] = planned?.split(':') ?? [];
  if (items[item] && policyAllows(item) && step < plan.length) {
    const target = item === 'revival'
      ? actor.side.pokemon.find(p => p.auditCode === 'k' && p.fainted && actorCode === code)
      : actor;
    if (target) {
      pending.set(actor, {item, target});
      return options[0].choice;
    }
  }

  const selected = options.find(option => option.id === planned && (policy === 'C' || option.move.category !== 'Status'));
  if (selected) return selected.choice;
  return options.reduce((best, option) =>
    attackScore(battle, actor, option) > attackScore(battle, actor, best) ? option : best
  ).choice;
}

function simulate(entry, seed, scenario, strategy) {
  const rivalRecovery = strategy?.reactive ? {potions:strategy.potions} : null;
  const coOp = !!entry.ally;
  const doubles = entry.opponents.length > 1;
  const baseFormat = Dex.formats.get('gen8bdspou');
  const format = {...baseFormat, gameType:doubles ? 'doubles' : 'singles', ruleTable:null, ruleset:['Team Preview'], banlist:[], rated:false};
  const battle = new Battle({format, seed, strictChoices:true});
  const pending = new Map();
  const steps = new Map();
  const evolutionState = new Set();
  const player = strategy?.reviveFainted ? entry.party : entry.party.filter(mon => !mon.hp.startsWith('0/'));
  const allyTeam = entry.ally?.party ?? [];
  const playerBoard = coOp ? [player[0], allyTeam[0], ...player.slice(1), ...allyTeam.slice(1)] : player;
  const enemy = doubles
    ? [...entry.opponents.map(t => t.party[0]), ...entry.opponents.flatMap(t => t.party.slice(1))]
    : entry.opponents[0].party;
  battle.setPlayer('p1',{team:playerBoard.map(mon => makeSet(mon, true))});
  battle.setPlayer('p2',{team:enemy.map(mon => makeSet(mon, false))});
  for (const [i, pokemon] of battle.p1.pokemon.entries()) {
    const mon = playerBoard[i];
    pokemon.auditCode = mon.code ?? 'ally';
    if (mon.code) {
      setEntry(pokemon, mon, entry.key, scenario);
      if (strategy?.startFull) pokemon.hp = pokemon.maxhp;
    }
  }
  battle.p2.pokemon.forEach((pokemon, i) => {pokemon.auditSlot = i;});
  if (entry.field === 'hail') {
    battle.field.setWeather('hail', battle.p1.pokemon[0]);
    battle.field.weatherState.duration = 0;
  }
  if (entry.field === 'fog') {
    const original = battle.runEvent.bind(battle);
    battle.runEvent = function(event, target, source, effect, value, ...args) {
      const result = original(event, target, source, effect, value, ...args);
      return event === 'Accuracy' && typeof result === 'number' ? result * 0.6 : result;
    };
  }
  const resolve = battle.queue.resolveAction.bind(battle.queue);
  battle.queue.resolveAction = function(action, ...args) {
    if (action.choice === 'move' && pending.has(action.pokemon)) {
      action.choice = 'bag';
      action.order = 102;
      action.bag = pending.get(action.pokemon);
      delete action.move;
      delete action.moveid;
    }
    return resolve(action, ...args);
  };
  const runAction = battle.runAction.bind(battle);
  battle.runAction = function(action) {
    if (action.choice === 'bag') {
      const {target, item} = action.bag;
      pending.delete(action.pokemon);
      bagAction(battle, target, item);
    }
    const result = runAction(action);
    for (const opponent of battle.p2.pokemon) {
      if (!opponent.fainted || evolutionState.has(opponent)) continue;
      evolutionState.add(opponent);
      const growth = faintLevels[entry.key]?.[opponent.species.id];
      if (!growth) continue;
      for (const pokemon of battle.p1.pokemon) {
        if (!growth.includes(pokemon.auditCode) || !pokemon.hp) continue;
        const old = battle.spreadModify(pokemon.species.baseStats, pokemon.set);
        pokemon.level++;
        pokemon.set.level++;
        const next = battle.spreadModify(pokemon.species.baseStats, pokemon.set);
        pokemon.maxhp += next.hp - old.hp;
        pokemon.baseMaxhp = pokemon.maxhp;
        pokemon.hp += next.hp - old.hp;
        for (const stat of statNames.slice(1)) pokemon.storedStats[stat] = pokemon.baseStoredStats[stat] = next[stat];
      }
    }
    return result;
  };
  const order = team => 'team ' + team.map((_, i) => i + 1).join('');
  battle.choose('p1',order(playerBoard));
  battle.choose('p2',order(enemy));
  let medicine = leaderMedicines[entry.key]?.[1] ?? 0;
  for (let i = 0; !battle.ended && i < 180; i++) {
    if (policy === 'C' && entry.key === '241' && battle.p1.activeRequest?.active && battle.p2.activeRequest?.active) {
      const opponent = battle.p2.active[0];
      const stepKey = 'p1:' + opponent?.auditSlot;
      const support = battle.p1.pokemon.find(mon => mon.auditCode === 'm' && mon.hp && !mon.isActive);
      if (opponent?.species.id === 'quagsire' && support && !steps.has(stepKey)) {
        steps.set(stepKey, 1);
        battle.actions.switchIn(support, 0, null, true);
        battle.makeRequest('move');
      }
    }
    for (const side of battle.sides) {
      const req = side.activeRequest;
      if (!req || req.wait) continue;
      const playerSide = side.id === 'p1';
      let choice;
      if (req.forceSwitch) {
        const bench = side.pokemon.filter(mon => mon.hp && !mon.isActive);
        choice = req.forceSwitch.map(required => {
          const mon = required ? bench.shift() : null;
          return mon ? 'switch ' + (mon.position + 1) : 'pass';
        }).join(', ');
      } else {
        choice = req.active.map((request, n) => {
          const mon = side.active[n];
          if (!mon?.hp || !request) return 'pass';
          const options = available(battle, mon, request);
          if (playerSide) return playerChoice(battle, entry, mon, options, steps, pending, mon.auditCode, rivalRecovery);
          if (medicine > 0 && mon.hp > 1 && mon.hp < mon.maxhp / 4) {
            medicine--;
            pending.set(mon, {item:leaderMedicines[entry.key][0], target:mon});
            return options[0].choice;
          }
          const trace = npcOpenings[entry.key]?.[mon.species.id];
          if (!scenario && trace) {
            const key = 'p2:' + mon.auditSlot;
            const index = steps.get(key) ?? 0;
            steps.set(key, index + 1);
            const replay = options.find(option => option.id === trace[index]);
            if (replay) return replay.choice;
          }
          return chooseNpc(battle, mon, options, scenario, entry.tactical).choice;
        }).join(', ');
      }
      battle.choose(side.id, choice);
    }
  }
  if (process.env.BDSP_TRACE) process.stderr.write(battle.log.join('\n') + '\n');
  return !battle.ended ? 'unresolved' : battle.winner === battle.p1.name ? 'win' : 'loss';
}

function prepare(entry) {
  entry.tactical = entry.opponents.some(t => /Leader|Commander| Boss |Elite Four|Champion|Cedric/.test(t.name));
  const log = toID(entry.log);
  const names = new Map(entry.party.flatMap(mon => mon.moves.map(name => [toID(name), name])));
  const candidates = [...names.keys()].filter(id => log.includes(id) && dex.moves.get(id).category !== 'Status');
  if (candidates.length === 1) entry.attack = candidates[0];
  return entry;
}

function countResults(entry, trials, strategy) {
  prepare(entry);
  return [0,1].map(scenario => {
    const counts = {win:0,loss:0,unresolved:0};
    for (let trial = 0; trial < trials; trial++) {
      const seed = [entry.number, 9973 * (scenario + 1), trial + 1, 13007];
      counts[simulate(entry, seed, scenario, strategy)]++;
    }
    return counts;
  });
}

function run(trials, only) {
  return fixtures.filter(entry => !only || only.has(entry.key)).map(entry => {
    if (entry.goal !== 'defeat') return {key:entry.key, goal:entry.goal, ...(entry.key === 'palkia' ? {guaranteed:100} : {})};
    return {key:entry.key, trials, results:countResults(entry, trials)};
  });
}

function route203Sensitivity(trials) {
  const entry = fixtures.find(encounter => encounter.key === '178');
  // The bag shows ten Potions against Piplup. Using one before entry leaves nine.
  const variants = [
    {strategy:'recorded', startFull:false, reactive:false},
    {strategy:'full-hp-recorded-actions', startFull:true, reactive:false},
    {strategy:'reactive-recovery', startFull:false, reactive:true, potions:10},
    {strategy:'preheal-and-reactive-recovery', startFull:true, reactive:true, potions:9},
  ];
  return variants.map(variant => ({...variant, trials, results:countResults(entry, trials, variant)}));
}

function healingSensitivity(trials, keys) {
  if (!keys.length || new Set(keys).size !== keys.length) throw Error('Specify unique defeat encounter IDs');
  return keys.map(key => {
    const entry = fixtures.find(encounter => encounter.key === key && encounter.goal === 'defeat');
    if (!entry) throw Error('Unknown defeat encounter: ' + key);
    const variants = [{strategy:'recorded'}];
    const living = entry.party.filter(mon => !mon.hp.startsWith('0/'));
    const injured = living.some(mon => {
      const [hp, maxhp] = mon.hp.split('/');
      return !maxhp || hp !== maxhp;
    });
    if (injured) variants.push({strategy:'heal-living', startFull:true});
    if (living.length < entry.party.length) variants.push({strategy:'restore-all', startFull:true, reviveFainted:true});
    return {
      key, trials,
      entryHp: entry.party.map(mon => ({name:mon.name, hp:mon.hp})),
      variants: variants.map(variant => ({
        strategy:variant.strategy,
        results:countResults(entry, trials, variant),
      })),
    };
  });
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const route203 = args[0] === '--route-203';
  const healing = args[0] === '--entry-healing';
  const [count = '128', ...keys] = route203 || healing ? args.slice(1) : args;
  const trials = Number(count);
  if (!Number.isSafeInteger(trials) || trials < 1 || trials > 65534) throw Error('Expected 1–65534 trials per scenario');
  if (route203 && (policy === 'A' || keys.length)) throw Error('Route 203 sensitivity requires B or C and a trial count only');
  const output = route203 ? route203Sensitivity(trials)
    : healing ? healingSensitivity(trials, keys)
    : run(trials, keys.length ? new Set(keys) : null);
  process.stdout.write(JSON.stringify(output, null, 2) + '\n');
}

module.exports = {dex, fixtures, makeSet, statNames};
