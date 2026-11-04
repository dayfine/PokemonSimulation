/** FireRed/LeafGreen (Gen 3) damage previews, including stat stages and measured raw stats.
 * Attack/Sp. Atk and Defense/Sp. Def stages are applied by Smogon, with its
 * Gen 3 critical-hit rules. Do not pre-apply stages to storedStats: that would
 * count them twice and prevent critical hits from ignoring the right stages.
 * Speed stages feed Showdown's getStat('spe') in engine.cjs, not damage rolls.
 * Accuracy/evasion use the separate FRLG stage table below; HP has no stage.
 */
'use strict';
const calc = require('@smogon/calc');
const GEN = calc.Generations.get(3);
const PREVIEW_CACHE = new Map();
const CACHE_LIMIT = 16384;

function previewKey(attacker, defender, name, crit) {
  // Exactly the inputs consumed by MeasuredPokemon and calc.Field below.
  const mon = p => [p.species.name, p.level, p.getAbility().name, p.set.nature,
    p.gender, p.getItem().name, p.status, p.boosts, p.hp, p.maxhp, p.storedStats,
    !!p.side.sideConditions.reflect, !!p.side.sideConditions.lightscreen];
  return JSON.stringify([mon(attacker), mon(defender), name, crit, attacker.battle.field.weather]);
}

class MeasuredPokemon extends calc.Pokemon {
  constructor(pokemon) {
    super(GEN, pokemon.species.name, {
      level: pokemon.level, ability: pokemon.getAbility().name,
      nature: pokemon.set.nature, gender: pokemon.gender, item: pokemon.getItem().name,
      status: pokemon.status, boosts: {...pokemon.boosts}, curHP: pokemon.hp,
    });
    this.source = pokemon;
    this.rawStats = {hp: pokemon.maxhp, ...pokemon.storedStats};
    this.stats = {...this.rawStats};
    this.originalCurHP = pokemon.hp;
  }
  // calculate() clones both combatants. The default clone recalculates stats
  // from IVs/EVs and would silently discard measured summary values.
  clone() { return new MeasuredPokemon(this.source); }
}

function rolls(attacker, defender, name, crit = false) {
  const key = previewKey(attacker, defender, name, crit);
  if (PREVIEW_CACHE.has(key)) return PREVIEW_CACHE.get(key);
  const result = calculateRolls(attacker, defender, name, crit);
  if (PREVIEW_CACHE.size >= CACHE_LIMIT) PREVIEW_CACHE.delete(PREVIEW_CACHE.keys().next().value);
  PREVIEW_CACHE.set(key, Object.freeze(result));
  return result;
}

function calculateRolls(attacker, defender, name, crit) {
  const move = new calc.Move(GEN, name, {isCrit: crit, hits: 1});
  move.hits = 1;
  const battle = attacker.battle;
  const weather = {raindance: 'Rain', sunnyday: 'Sun', sandstorm: 'Sand', hail: 'Hail'}[battle.field.weather];
  const side = pokemon => ({isReflect: !!pokemon.side.sideConditions.reflect,
    isLightScreen: !!pokemon.side.sideConditions.lightscreen});
  const field = new calc.Field({weather, attackerSide: side(attacker), defenderSide: side(defender)});
  const result = calc.calculate(GEN, new MeasuredPokemon(attacker), new MeasuredPokemon(defender), move, field);
  if (typeof result.damage === 'number') return [result.damage];
  const count = battle.dex.moves.get(name).multihit;
  if (!count) return result.damage;
  const perHit = Array.isArray(result.damage[0]) ? result.damage[0] : result.damage;
  // Small exact convolutions, then equally weighted quantiles for policy use.
  // Showdown samples actual hit count/damage; previews never draw battle RNG.
  const weights = Array.isArray(count) ? [[2, 3 / 8], [3, 3 / 8], [4, 1 / 8], [5, 1 / 8]] : [[count, 1]];
  const distribution = new Map();
  for (const [hits, weight] of weights) {
    let sums = new Map([[0, 1]]);
    for (let hit = 0; hit < hits; hit++) {
      const next = new Map();
      for (const [sum, probability] of sums) for (const damage of perHit) {
        next.set(sum + damage, (next.get(sum + damage) || 0) + probability / perHit.length);
      }
      sums = next;
    }
    for (const [sum, probability] of sums) distribution.set(sum, (distribution.get(sum) || 0) + probability * weight);
  }
  const sorted = [...distribution].sort((a, b) => a[0] - b[0]);
  return Array.from({length: 32}, (_, i) => {
    let cumulative = 0;
    for (const [damage, probability] of sorted) {
      cumulative += probability;
      if (cumulative >= (i + 0.5) / 32) return damage;
    }
    return sorted.at(-1)[0];
  });
}

function accuracy(attacker, defender, move) {
  if (move.accuracy === true) return 1;
  const ratios = [33, 36, 43, 50, 60, 75, 100, 133, 166, 200, 233, 266, 300];
  const stage = Math.max(-6, Math.min(6, attacker.boosts.accuracy - defender.boosts.evasion));
  return Math.min(1, Math.floor(move.accuracy * ratios[stage + 6] / 100) / 100);
}

function movePreview(pokemon, target, slot) {
  const move = pokemon.battle.dex.moves.get(slot.id);
  const damaging = move.category !== 'Status';
  const damage = damaging ? rolls(pokemon, target, move.name) : [0];
  const critical = damaging ? rolls(pokemon, target, move.name, true) : [0];
  const effectiveness = pokemon.battle.dex.getImmunity(move.type, target) ?
    2 ** pokemon.battle.dex.getEffectiveness(move.type, target) : 0;
  return {id: move.id, name: move.name, pp: slot.pp, max_pp: slot.maxpp,
    disabled: !!slot.disabled, power: move.basePower, type: move.type,
    category: move.category, priority: move.priority, accuracy: accuracy(pokemon, target, move),
    two_turn: !!move.flags.charge, effectiveness, damage, critical};
}
module.exports = {rolls, accuracy, movePreview};
