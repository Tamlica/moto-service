// Plain-language part notes for everyday riders.
export const PARTS = {
  engine_oil: { label: 'Engine oil', why: 'Oil keeps the engine from grinding itself apart. Old oil thins out and stops protecting it.' },
  oil_filter: { label: 'Oil filter', why: 'Catches metal grit from the oil. A clogged filter lets dirty oil circulate.' },
  gear_oil: { label: 'Gear oil', why: 'Lubricates the final-drive gears in the rear hub of a scooter. Cheap to change, expensive to ignore.' },
  cvt_belt: { label: 'CVT belt', why: 'The rubber belt that drives the rear wheel. A worn belt slips, then snaps and leaves you stranded.' },
  chain: { label: 'Chain', why: 'A dry or loose chain wears out sprockets fast and can jump off. Clean and lube it often.' },
  air_filter: { label: 'Air filter', why: 'A dirty filter chokes the engine: less power, more fuel used.' },
  spark_plug: { label: 'Spark plug', why: 'Lights the fuel. A worn plug means hard starts and rough idle.' },
  brake_front: { label: 'Front brake', why: 'Does most of your stopping. Thin pads can score the disc and lengthen stopping distance.' },
  brake_rear: { label: 'Rear brake', why: 'Worn pads or shoes make the rear brake weak and noisy.' },
  brake_fluid: { label: 'Brake fluid', why: 'Absorbs water over time, which makes the lever spongy. Change it every couple of years.' },
  coolant: { label: 'Coolant', why: 'Keeps a liquid-cooled engine from overheating. It breaks down with age.' },
  tire_front: { label: 'Front tire', why: 'Grip and steering. Check tread depth, cracks, and pressure every week or two.' },
  tire_rear: { label: 'Rear tire', why: 'Wears faster than the front. Bald tires are dangerous in the rain.' },
  battery: { label: 'Battery', why: 'A weak battery shows up first as a slow electric start, then no start at all.' },
  general: { label: 'General check', why: 'Lights, horn, cables, bolts, tire pressure. Ten minutes that catch most problems early.' },
};
export const PART_IDS = Object.keys(PARTS);
