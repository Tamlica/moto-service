// Line-art blueprint data for the four bike types.
// Coordinates live in a 1000x520 drawing space, front of the bike on the right, ground at y≈470.
// Every bike: { frame: Shape[], parts: Part[], center: [x,y] }
//   Shape = [tag, attrs]   (rendered with <svelte:element>)
//   Part  = { id, at: [x,y], shapes: Shape[] }   id matches tasks.part on the server.
// Swap in nicer artwork any time; keep the part ids.

const C = (cx, cy, r) => ['circle', { cx, cy, r }];
const P = (d) => ['path', { d }];
const L = (x1, y1, x2, y2) => ['line', { x1, y1, x2, y2 }];
const rad = (deg) => (deg * Math.PI) / 180;
const onWheel = (cx, cy, r, deg) => [Math.round(cx + r * Math.cos(rad(deg))), Math.round(cy + r * Math.sin(rad(deg)))];
const arc = (cx, cy, r, a0, a1) => {
  const [x0, y0] = onWheel(cx, cy, r, a0);
  const [x1, y1] = onWheel(cx, cy, r, a1);
  return P(`M ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1}`);
};
const rect = (x, y, w, h) => P(`M ${x} ${y} h ${w} v ${h} h ${-w} Z`);

function wheel(cx, cy, r, spokes = 5) {
  const inner = Math.round(r * 0.74);
  const s = [C(cx, cy, r), C(cx, cy, r - 8), C(cx, cy, inner), C(cx, cy, 6)];
  for (let i = 0; i < spokes; i++) {
    const a = (360 / spokes) * i - 90;
    const [x0, y0] = onWheel(cx, cy, 10, a);
    const [x1, y1] = onWheel(cx, cy, inner, a);
    s.push(L(x0, y0, x1, y1));
  }
  return s;
}

function tire(id, cx, cy, r, deg) {
  return { id, at: onWheel(cx, cy, r, deg), shapes: [arc(cx, cy, r, deg - 22, deg + 22), arc(cx, cy, r - 8, deg - 22, deg + 22)] };
}

function brakeFluid(x, y) {
  return { id: 'brake_fluid', at: [x, y], shapes: [rect(x - 11, y - 6, 22, 12), L(x + 11, y, x + 30, y + 4)] };
}

function plug(x, y) {
  return { id: 'spark_plug', at: [x, y], shapes: [P(`M ${x - 4} ${y + 12} L ${x + 2} ${y - 4} M ${x - 6} ${y - 4} L ${x + 10} ${y - 2}`)] };
}

const scooter = {
  center: [520, 330],
  frame: [
    ...wheel(360, 412, 58, 5),
    ...wheel(700, 412, 58, 5),
    P('M 270 330 Q 268 282 322 268 L 540 272 Q 566 276 566 304 L 566 372 L 626 372 L 646 214 Q 650 192 676 186 L 690 184'),
    P('M 690 184 Q 728 224 724 286 L 714 350'),
    P('M 566 372 L 566 390 L 628 390 L 626 372'),
    P('M 286 380 Q 350 336 430 362'),
    P('M 648 372 Q 700 338 752 372'),
    P('M 316 268 Q 316 240 348 238 L 516 240 Q 544 242 548 270'),
    L(676, 186, 666, 140),
    L(626, 140, 712, 140),
    L(648, 140, 636, 104),
    L(620, 100, 652, 100),
    L(680, 214, 700, 412),
    P('M 722 230 Q 740 238 734 258 L 720 260'),
    P('M 270 300 L 258 304 L 260 322 L 270 322'),
    P('M 340 400 Q 336 372 362 368 L 492 354 Q 522 352 524 378 Q 526 402 496 406 L 362 420 Q 340 420 340 400 Z'),
    P('M 492 354 L 506 318 L 556 324 L 546 360'),
  ],
  parts: [
    { id: 'engine_oil', at: [528, 386], shapes: [C(528, 386, 7), P('M 514 360 l -6 -16')] },
    { id: 'gear_oil', at: [398, 404], shapes: [C(398, 404, 7)] },
    { id: 'cvt_belt', at: [452, 378], shapes: [C(382, 398, 13), C(496, 380, 17), P('M 382 385 L 496 363 M 382 411 L 496 397')] },
    { id: 'air_filter', at: [433, 334], shapes: [rect(396, 324, 74, 22)] },
    plug(530, 310),
    { id: 'battery', at: [596, 300], shapes: [rect(580, 288, 32, 24), P('M 588 288 v -5 M 604 288 v -5')] },
    { id: 'coolant', at: [664, 262], shapes: [rect(656, 248, 16, 28), L(656, 258, 672, 258)] },
    { id: 'brake_front', at: [700, 412], shapes: [C(700, 412, 26), P('M 714 386 q 14 6 14 22')] },
    { id: 'brake_rear', at: [360, 412], shapes: [C(360, 412, 20)] },
    brakeFluid(634, 128),
    tire('tire_front', 700, 412, 58, 40),
    tire('tire_rear', 360, 412, 58, 140),
  ],
};

const underbone = {
  center: [530, 320],
  frame: [
    ...wheel(350, 404, 66, 12),
    ...wheel(720, 404, 66, 12),
    P('M 664 196 Q 610 260 560 318 Q 540 340 500 344'),
    L(662, 200, 712, 404),
    L(676, 198, 728, 402),
    P('M 640 156 L 700 150'),
    L(664, 188, 668, 154),
    L(650, 154, 640, 118),
    L(626, 116, 656, 116),
    P('M 676 168 Q 712 176 712 206 L 684 214'),
    P('M 646 214 Q 636 290 590 338'),
    P('M 676 360 Q 722 320 772 352'),
    P('M 300 270 Q 302 248 330 246 L 540 250 Q 562 252 566 276'),
    P('M 280 300 Q 282 276 306 272 L 560 278 L 548 318 L 360 324 Q 300 326 280 300 Z'),
    P('M 300 376 Q 350 324 412 350'),
    L(486, 350, 354, 398),
    L(490, 364, 356, 410),
    P('M 470 372 Q 466 340 498 334 L 560 332 Q 590 334 594 356 L 592 384 Q 586 404 560 404 L 500 404 Q 470 402 470 372 Z'),
    P('M 594 342 L 640 334 L 646 366 L 594 374'),
    P('M 646 368 Q 650 420 600 428 L 420 432'),
    P('M 420 420 L 330 418 Q 316 420 316 432 Q 318 444 332 444 L 420 444 Z'),
  ],
  parts: [
    { id: 'engine_oil', at: [516, 394], shapes: [C(516, 394, 7), P('M 556 334 l 4 -16')] },
    { id: 'oil_filter', at: [572, 368], shapes: [C(572, 368, 10), C(572, 368, 4)] },
    { id: 'chain', at: [420, 384], shapes: [C(488, 372, 12), C(350, 404, 26), P('M 488 360 L 350 378 M 488 384 L 350 430')] },
    { id: 'air_filter', at: [500, 302], shapes: [rect(470, 292, 60, 20)] },
    { id: 'battery', at: [420, 300], shapes: [rect(404, 290, 32, 20), P('M 412 290 v -5 M 428 290 v -5')] },
    plug(640, 320),
    { id: 'brake_front', at: [720, 404], shapes: [C(720, 404, 22), P('M 736 384 q 10 8 8 22')] },
    { id: 'brake_rear', at: [350, 404], shapes: [C(350, 404, 13)] },
    brakeFluid(646, 146),
    tire('tire_front', 720, 404, 66, 40),
    tire('tire_rear', 350, 404, 66, 140),
  ],
};

const sport = {
  center: [520, 310],
  frame: [
    ...wheel(330, 400, 70, 6),
    ...wheel(720, 400, 70, 6),
    P('M 470 236 Q 480 196 540 192 L 600 196 Q 628 204 632 236 L 600 266 L 486 262 Z'),
    P('M 470 238 L 340 236 Q 300 232 270 214 L 300 210 Q 340 222 380 222 L 470 224'),
    P('M 270 214 L 262 232 L 340 252 L 470 258'),
    L(642, 194, 712, 400),
    L(656, 190, 728, 398),
    P('M 620 168 L 690 160'),
    L(650, 190, 654, 164),
    L(640, 164, 626, 128),
    L(612, 126, 642, 126),
    P('M 670 196 Q 704 196 708 226 Q 704 248 680 250'),
    P('M 650 194 L 480 270 L 470 336 M 650 212 L 610 300 M 560 232 L 600 300 M 530 248 L 540 290'),
    L(470, 336, 330, 400),
    L(476, 350, 334, 412),
    P('M 674 344 Q 724 312 776 344'),
    P('M 300 344 Q 330 316 380 330'),
    P('M 470 340 L 476 300 L 560 290 L 610 300 L 616 360 Q 610 392 580 396 L 500 396 Q 470 392 470 360 Z'),
    P('M 560 290 L 572 264 L 620 270 L 612 300'),
    P('M 612 380 Q 600 432 540 432 L 470 430'),
    P('M 470 420 L 410 418 Q 398 424 404 436 L 470 440 Z'),
  ],
  parts: [
    { id: 'engine_oil', at: [500, 382], shapes: [C(500, 382, 7), P('M 486 300 l -4 -14')] },
    { id: 'oil_filter', at: [590, 372], shapes: [C(590, 372, 10), C(590, 372, 4)] },
    { id: 'chain', at: [400, 380], shapes: [C(476, 356, 12), C(330, 400, 28), P('M 476 344 L 330 372 M 476 368 L 330 428')] },
    { id: 'air_filter', at: [517, 277], shapes: [rect(492, 268, 50, 18)] },
    plug(596, 260),
    { id: 'coolant', at: [636, 308], shapes: [P('M 626 270 L 652 274 L 642 346 L 616 342 Z'), P('M 630 290 L 646 292 M 627 310 L 643 312 M 624 330 L 640 332')] },
    { id: 'battery', at: [420, 246], shapes: [rect(404, 238, 32, 16)] },
    { id: 'brake_front', at: [720, 400], shapes: [C(720, 400, 30), P('M 738 372 q 16 8 16 26')] },
    { id: 'brake_rear', at: [330, 400], shapes: [C(330, 400, 18)] },
    brakeFluid(628, 156),
    tire('tire_front', 720, 400, 70, 40),
    tire('tire_rear', 330, 400, 70, 140),
  ],
};

const trail = {
  center: [530, 300],
  frame: [
    ...wheel(330, 392, 74, 14),
    ...wheel(740, 386, 80, 14),
    P('M 330 214 L 560 204 Q 576 204 580 214 L 560 226 L 340 232 Z'),
    P('M 560 206 L 610 196 Q 640 200 646 222 L 620 262 L 560 250'),
    P('M 330 222 L 220 196 L 230 208 L 340 236'),
    P('M 700 230 L 800 236 L 782 246 L 712 244'),
    P('M 690 206 Q 716 206 722 236 L 702 258 L 690 240 Z'),
    L(668, 178, 736, 384),
    L(684, 174, 750, 382),
    P('M 640 150 L 716 140'),
    L(674, 176, 678, 146),
    P('M 676 180 L 560 250 L 500 330 M 676 196 L 610 300 M 560 250 L 520 232'),
    L(500, 336, 330, 392),
    L(506, 350, 334, 404),
    L(450, 232, 494, 320),
    P('M 500 336 Q 496 300 530 296 L 590 294 Q 618 298 618 330 L 614 360 Q 604 380 576 380 L 530 380 Q 502 376 500 350 Z'),
    P('M 540 296 L 548 258 L 600 262 L 596 296'),
    P('M 600 284 Q 650 296 622 330 Q 560 384 470 300 L 420 258'),
    P('M 420 246 L 330 226 L 326 242 L 410 262 Z'),
    P('M 520 384 L 610 380 L 620 366'),
  ],
  parts: [
    { id: 'engine_oil', at: [540, 368], shapes: [C(540, 368, 7), P('M 528 296 l -4 -14')] },
    { id: 'oil_filter', at: [602, 340], shapes: [C(602, 340, 10), C(602, 340, 4)] },
    { id: 'chain', at: [420, 380], shapes: [C(506, 346, 12), C(330, 392, 30), P('M 506 334 L 330 362 M 506 358 L 330 422')] },
    { id: 'air_filter', at: [468, 248], shapes: [rect(440, 238, 56, 22)] },
    { id: 'battery', at: [519, 226], shapes: [rect(504, 218, 30, 16)] },
    plug(572, 250),
    { id: 'brake_front', at: [740, 386], shapes: [C(740, 386, 32), P('M 760 360 q 14 10 12 28')] },
    { id: 'brake_rear', at: [330, 392], shapes: [C(330, 392, 20)] },
    brakeFluid(652, 146),
    tire('tire_front', 740, 386, 80, 40),
    tire('tire_rear', 330, 392, 74, 140),
  ],
};

export const BIKES = { scooter, underbone, sport, trail };
export const BIKE_TYPES = [
  { id: 'scooter', label: 'Scooter', hint: 'Automatic, CVT belt (Vario, NMAX, Beat)' },
  { id: 'underbone', label: 'Underbone', hint: 'Step-through with chain (Supra, Jupiter)' },
  { id: 'sport', label: 'Sport / naked', hint: 'Manual, tank between knees (CB150R, Vixion)' },
  { id: 'trail', label: 'Trail', hint: 'Tall, long-travel, off-road (KLX, CRF)' },
];
