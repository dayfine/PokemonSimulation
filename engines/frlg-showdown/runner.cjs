/** FireRed/LeafGreen (Gen 3) adapter JSON-lines protocol; stdout contains responses only. */
'use strict';
const readline = require('node:readline');
const {createBattle, playTurn, snapshot} = require('./engine.cjs');
let battle;
const lines = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
lines.on('line', line => {
  try {
    const request = JSON.parse(line);
    let logStart = battle?.log.length || 0;
    if (request.command === 'start') {
      if (battle) battle.destroy();
      battle = createBattle(request.scenario, request.seed);
      logStart = 0;
    } else if (request.command === 'step') {
      if (!battle || battle.ended) throw new Error('No active battle');
      playTurn(battle, request.own, request.foe);
    } else throw new Error(`Unknown command ${request.command}`);
    process.stdout.write(JSON.stringify({ok: true, state: snapshot(battle, logStart)}) + '\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({ok: false, error: error.message}) + '\n');
  }
});
