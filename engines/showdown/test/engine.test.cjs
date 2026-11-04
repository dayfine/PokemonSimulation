/** Integration checks for the FRLG adapter's mechanics boundaries. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {createBattle, playTurn, snapshot} = require('../engine.cjs');
const {rolls} = require('../damage.cjs');
const SEED = [1, 2, 3, 4];

function scenario(player = {}, foe = {}) {
  return {player: {species: 'Wartortle', level: 20, moves: ['Bite'],
    stats: {hp: 60, atk: 33, def: 40, spa: 34, spd: 40, spe: 31}, ...player},
    bag: {potion: 2, superpotion: 1, awakening: 1}, badges: ['boulder'],
    trainer: {party: [{species: 'Abra', level: 16, moves: ['Teleport'], ...foe}], bag: {potion: 1}}};
}
const move = slot => ({kind: 'move', slot});
const item = name => ({kind: 'item', item: name});
function withoutCrits(battle) {
  const randomChance = battle.randomChance.bind(battle);
  battle.randomChance = (numerator, denominator) =>
    numerator === 1 && denominator >= 16 ? false : randomChance(numerator, denominator);
}

test('Potion is a turn action while asleep: healing, no PP or sleep decrement', () => {
  const b = createBattle(scenario({hp: 20, status: 'slp', sleep_turns: 4}), SEED);
  playTurn(b, item('potion'), move(0));
  const s = snapshot(b);
  assert.equal(s.turn, 2);
  assert.equal(s.own.hp, 40);
  assert.equal(s.own.sleep_turns, 4);
  assert.equal(s.own.moves[0].pp, 25);
  assert.equal(s.foe.moves[0].pp, 19);
  assert.equal(s.bag.potion, 1);
  assert.equal(s.items_used.potion, 1);
  assert.ok(s.log.some(l => l.includes('|switch|p1a: Wartortle|') && l.includes('20/60')));
  b.destroy();
});

test('bag healing precedes a faster priority attack and still permits poison residuals', () => {
  const b = createBattle(scenario({hp: 10, status: 'psn'}, {species: 'Rattata', moves: ['Quick Attack']}), SEED);
  withoutCrits(b); // No critical hit; damage still has its random roll.
  playTurn(b, item('superpotion'), move(0));
  const log = snapshot(b).log;
  assert.ok(log.findIndex(l => l.includes('used superpotion')) < log.findIndex(l => l.startsWith('|move|')));
  assert.ok(log.some(l => l.includes('[from] psn')));
  assert.equal(b.p1.active[0].status, 'psn');
  assert.ok(b.p1.active[0].hp > 10);
  b.destroy();
});

test('both trainers may use bag items on the same turn without phantom moves', () => {
  const s = scenario({hp: 20}, {status: 'slp', sleep_turns: 4, hp: 10});
  const b = createBattle(s, SEED);
  playTurn(b, item('potion'), item('potion'));
  const after = snapshot(b);
  assert.equal(after.turn, 2);
  assert.equal(after.own.hp, 40);
  assert.equal(after.foe.sleep_turns, 4);
  assert.equal(after.foe.moves[0].pp, 20);
  assert.equal(after.trainer_bag.potion, 0);
  assert.equal(after.log.filter(l => l.startsWith('|move|')).length, 0);
  b.destroy();
});

test('Awakening removes sleep and costs the turn without using an attack', () => {
  const b = createBattle(scenario({status: 'slp', sleep_turns: 4}), SEED);
  playTurn(b, item('awakening'), move(0));
  assert.equal(b.p1.active[0].status, '');
  assert.equal(b.p1.active[0].moveSlots[0].pp, 25);
  assert.equal(b.p1.pokesimBag.awakening, 0);
  b.destroy();
});

test('Dig requires two turns, spends one PP, and cannot be interrupted by an item', () => {
  const b = createBattle(scenario({moves: ['Dig']}), SEED);
  withoutCrits(b);
  const originalHP = b.p2.active[0].hp;
  playTurn(b, move(0), move(0));
  assert.equal(b.p2.active[0].hp, originalHP);
  assert.equal(b.p1.active[0].moveSlots[0].pp, 9);
  assert.equal(snapshot(b).own.locked_move, 'dig');
  assert.equal(snapshot(b).own.moves[0].two_turn, true);
  assert.throws(() => playTurn(b, item('potion'), move(0)), /cannot be interrupted/);
  playTurn(b, move(0), move(0));
  assert.ok(b.p2.active[0].hp < originalHP);
  assert.equal(b.p1.active[0].moveSlots[0].pp, 9);
  b.destroy();
});

test('measured stats and no-PP-Up inputs survive both engine and damage previews', () => {
  const b = createBattle(scenario({moves: [{name: 'Bite', pp: 7}]}), SEED);
  const own = b.p1.active[0], foe = b.p2.active[0];
  const preview = rolls(own, foe, 'Bite');
  // Hand Gen 3 damage for Bite: Lv20, SpA34 vs Abra SpD25, power60,
  // super-effective, no STAB. floor(floor(10*60*34/25)/50)+2 = 18; 2x = 36.
  assert.equal(Math.max(...preview), 36);
  withoutCrits(b);
  const hp = foe.hp;
  playTurn(b, move(0), move(0));
  const dealt = hp - foe.hp;
  assert.ok(preview.includes(dealt) || foe.hp === 0);
  assert.equal(own.moveSlots[0].maxpp, 25);
  assert.equal(own.moveSlots[0].pp, 6);
  b.destroy();
});

test('badges affect battle damage without changing supplied summary stats', () => {
  const s = scenario({moves: ['Dig']}, {species: 'Raichu', level: 24, moves: ['Shock Wave']});
  const plain = createBattle({...s, badges: []}, SEED);
  const badge = createBattle(s, SEED);
  assert.equal(s.player.stats.atk, 33);
  assert.equal(badge.p1.active[0].storedStats.atk, 36);
  assert.ok(Math.max(...rolls(badge.p1.active[0], badge.p2.active[0], 'Dig')) >
    Math.max(...rolls(plain.p1.active[0], plain.p2.active[0], 'Dig')));
  plain.destroy(); badge.destroy();
});

test('Double Team lowers Dig accuracy, while Shock Wave remains accurate', () => {
  const b = createBattle(scenario({moves: ['Dig']}, {species: 'Raichu', moves: ['Double Team', 'Shock Wave']}), SEED);
  b.p2.active[0].boostBy({evasion: 2});
  b.p1.active[0].boostBy({evasion: 4});
  const s = snapshot(b);
  assert.equal(s.own.moves[0].accuracy, 0.6);
  assert.equal(s.foe.moves[1].accuracy, 1);
  b.destroy();
});

test('Torrent and Water Pulse confusion are active mechanics', () => {
  const b = createBattle(scenario({moves: ['Water Pulse']}, {species: 'Wartortle', level: 40, moves: ['Withdraw']}), [2, 2, 3, 4]);
  const own = b.p1.active[0], foe = b.p2.active[0];
  const healthy = Math.max(...rolls(own, foe, 'Water Pulse'));
  own.hp = Math.floor(own.maxhp / 3);
  assert.ok(Math.max(...rolls(own, foe, 'Water Pulse')) > healthy);
  playTurn(b, move(0), move(0));
  assert.ok(foe.volatiles.confusion);
  b.destroy();
});

test('same seed and actions produce identical traces, without wall-clock timestamps', () => {
  function run() {
    const b = createBattle(scenario(), SEED);
    playTurn(b, move(0), move(0));
    const s = snapshot(b); b.destroy(); return s;
  }
  assert.deepEqual(run(), run());
});

test('loss evidence survives Showdown faint cleanup, including Leech Seed and accuracy', () => {
  const b = createBattle(scenario({hp: 1, status: 'psn', moves: ['Withdraw']},
    {species: 'Raichu', level: 24, moves: ['Shock Wave']}), SEED);
  b.p1.active[0].addVolatile('leechseed', b.p2.active[0]);
  b.p1.active[0].boostBy({accuracy: -2});
  playTurn(b, move(0), move(0));
  const s = snapshot(b);
  assert.equal(s.winner, 'Trainer');
  assert.deepEqual(s.own.volatiles, []);
  assert.ok(s.own.faint.volatiles.includes('leechseed'));
  assert.equal(s.own.faint.boosts.accuracy, -2);
  assert.equal(s.own.faint.status, 'psn');
  assert.equal(s.own.faint.effect, 'shockwave');
  b.destroy();
});
