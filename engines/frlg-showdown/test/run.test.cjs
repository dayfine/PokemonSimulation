/** Exercise expanded FRLG bag actions, fields, locks and tutorial behavior. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {createBattle, playTurn, snapshot} = require('../engine.cjs');
const {rolls} = require('../damage.cjs');
const seed = [1, 2, 3, 4];
const move = slot => ({kind: 'move', slot});
const item = (name, slot) => ({kind: 'item', item: name, slot});
function scenario() {
  return {player: {species: 'Blastoise', level: 50, moves: ['Surf', 'Blizzard'],
    stats: {hp: 500, atk: 80, def: 80, spa: 80, spd: 80, spe: 60}},
    trainer: {party: [{species: 'Wartortle', level: 50, moves: ['Splash', 'Bounce'],
      stats: {hp: 500, atk: 50, def: 80, spa: 80, spd: 80, spe: 70}}]},
    bag: {xspecial: 8, xspeed: 1, xaccuracy: 1, guardspec: 1, ether: 1, elixir: 1}};
}

test('Gen 3 X items give one stage, cap at six, and cost turns without attack PP', () => {
  const b = createBattle(scenario(), seed);
  for (let i = 0; i < 7; i++) playTurn(b, item('xspecial'), move(0));
  assert.equal(b.p1.active[0].boosts.spa, 6);
  assert.equal(b.p1.active[0].moveSlots[0].pp, 15);
  assert.equal(b.p2.active[0].moveSlots[0].pp, 33);
  assert.equal(b.p1.pokesimBag.xspecial, 1);
  playTurn(b, item('xspeed'), move(0));
  assert.equal(snapshot(b).own.speed, 90);
  playTurn(b, item('xaccuracy'), move(0));
  assert.equal(snapshot(b).own.moves[1].accuracy, .93);
  b.destroy();
});

test('PP items restore selected or all slots and spend a turn', () => {
  const s = scenario(); s.player.moves = [{name: 'Surf', pp: 0}, {name: 'Blizzard', pp: 1}];
  const b = createBattle(s, seed);
  assert.throws(() => playTurn(b, item('ether'), move(0)), /requires a move slot/);
  playTurn(b, item('ether', 0), move(0));
  assert.deepEqual(b.p1.active[0].moveSlots.map(m => m.pp), [10, 1]);
  playTurn(b, item('elixir'), move(0));
  assert.deepEqual(b.p1.active[0].moveSlots.map(m => m.pp), [15, 5]);
  assert.equal(b.turn, 3);
  b.destroy();
});

test('Guard Spec blocks stat lowering for five turns including the use turn', () => {
  const s = scenario(); s.trainer.party[0].moves = ['Tail Whip']; s.player.moves = ['Splash', 'Splash'];
  const b = createBattle(s, seed);
  playTurn(b, item('guardspec'), move(0));
  for (let i = 0; i < 4; i++) playTurn(b, move(1), move(0));
  assert.equal(b.p1.active[0].boosts.def, 0);
  playTurn(b, move(1), move(0));
  assert.equal(b.p1.active[0].boosts.def, -1);
  b.destroy();
});

test('a locked move in the second slot maps to Showdown\'s single forced choice', () => {
  const b = createBattle(scenario(), seed);
  playTurn(b, move(0), move(1));
  assert.equal(snapshot(b).foe.locked_move, 'bounce');
  playTurn(b, move(0), move(1));
  assert.equal(b.p2.active[0].moveSlots[1].pp, 4);
  assert.equal(snapshot(b).foe.locked_move, '');
  b.destroy();
});

test('weather and screens affect previews; multi-hit previews remain numeric', () => {
  const b = createBattle(scenario(), seed), own = b.p1.active[0], foe = b.p2.active[0];
  const normal = rolls(own, foe, 'Surf');
  b.field.setWeather('raindance', own);
  const rain = rolls(own, foe, 'Surf');
  assert.ok(Math.min(...rain) > Math.max(...normal));
  foe.side.addSideCondition('lightscreen', foe);
  assert.ok(Math.max(...rolls(own, foe, 'Surf')) < Math.min(...rain));
  const single = rolls(own, foe, 'Tackle');
  const double = rolls(own, foe, 'Double Kick');
  assert.ok(single.every(Number.isFinite));
  assert.ok(double.every(Number.isFinite));
  assert.ok(rolls(own, foe, 'Fury Swipes').every(Number.isFinite));
  b.destroy();
});

test('Oak tutorial guarantees first player damaging accuracy and disables prior crits', () => {
  const s = scenario(); s.tutorial = true;
  s.player.moves = ['Tackle']; s.player.boosts = {accuracy: -6};
  const b = createBattle(s, seed);
  playTurn(b, move(0), move(0));
  assert.ok(b.pokesimTutorialDamage);
  assert.ok(!b.log.some(l => l.startsWith('|-miss|') || l.startsWith('|-crit|')));
  b.destroy();
});
