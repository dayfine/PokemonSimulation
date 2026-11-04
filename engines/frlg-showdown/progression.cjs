/** FRLG solo EXP/EV awards and level-up move decisions, from pinned pret data. */
'use strict';
const ORDER = ['hp', 'atk', 'def', 'spe', 'spa', 'spd'];
const id = value => value.toLowerCase().replace(/[^a-z0-9]/g, '');

function defeat(battle, foe) {
  const own = battle.p1.active[0];
  const data = own.pokesimProgression;
  if (!data || !own.hp || foe.side !== battle.p2 || foe.pokesimAwarded) return;
  foe.pokesimAwarded = true;
  const species = data.species[foe.species.id];
  if (!species) throw new Error(`Missing EXP/EV data for ${foe.species.id}`);
  for (const stat of ORDER) {
    const total = Object.values(data.evs).reduce((a, b) => a + b, 0);
    data.evs[stat] += Math.max(0, Math.min(species.ev_yield[stat], 255 - data.evs[stat], 510 - total));
  }
  const award = own.level === 100 ? 0 : Math.floor(Math.floor(species.exp_yield * foe.level / 7) * 150 / 100);
  data.exp += award;
  const before = own.level;
  while (own.level < 100 && data.exp >= data.thresholds[own.level + 1]) own.level++;
  const changes = [];
  if (own.level > before) {
    const lead = data.species[own.species.id];
    const raw = {};
    for (const stat of ORDER) {
      const value = Math.floor((2 * lead.base_stats[stat] + data.ivs[stat] + Math.floor(data.evs[stat] / 4)) * own.level / 100);
      raw[stat] = stat === 'hp' ? value + own.level + 10 : Math.floor((value + 5) * data.nature[stat] / 100);
    }
    own.hp += raw.hp - own.maxhp;
    own.maxhp = own.baseMaxhp = raw.hp;
    own.baseStoredStats = {...raw};
    for (const stat of ORDER.filter(s => s !== 'hp')) own.storedStats[stat] = raw[stat];
    const badgeStats = {boulder: ['atk'], soul: ['def'], volcano: ['spa', 'spd'], thunder: ['spe']};
    for (const badge of data.badges) for (const stat of badgeStats[badge] || []) {
      own.storedStats[stat] = Math.floor(raw[stat] * 110 / 100);
    }
    own.speed = own.getStat('spe');
    for (const offer of lead.learnset) {
      const name = id(offer.move);
      if (offer.level <= before || offer.level > own.level || own.moveSlots.some(m => m.id === name)) continue;
      const decision = data.decisions[name];
      if (!decision) throw new Error(`Missing level-up decision for ${name}`);
      if (decision.action === 'decline') continue;
      const move = battle.dex.moves.get(name);
      const slot = {move: move.name, id: name, pp: move.pp, maxpp: move.pp, target: move.target,
        disabled: false, disabledSource: '', used: false};
      if (decision.replaces) {
        const index = own.moveSlots.findIndex(m => m.id === id(decision.replaces));
        if (index < 0) throw new Error(`Cannot replace ${decision.replaces}`);
        own.moveSlots[index] = slot;
      } else if (own.moveSlots.length < 4) own.moveSlots.push(slot);
      else throw new Error(`No slot for ${name}`);
      own.baseMoveSlots = own.moveSlots.map(m => ({...m}));
      changes.push(name);
    }
    battle.add('-sethp', own, own.getHealth, '[silent]');
  }
  data.awards.push({foe: foe.species.id, party_index: foe.pokesimPartyIndex, exp: award,
    total_exp: data.exp, level_before: before, level_after: own.level, evs: {...data.evs}, learned: changes,
    raw_stats: {...own.baseStoredStats}, hp: own.hp});
}
module.exports = {defeat};
