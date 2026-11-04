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
  const move = new calc.Move(GEN, name, {isCrit: crit});
  const result = calc.calculate(GEN, new MeasuredPokemon(attacker), new MeasuredPokemon(defender), move);
  if (typeof result.damage === 'number') return [result.damage];
  if (result.damage.some(Array.isArray)) throw new Error('Multi-hit previews are outside this milestone');
  return result.damage;
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
