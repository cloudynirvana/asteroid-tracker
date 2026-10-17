import React from 'react';
import {AbsoluteFill, Audio, staticFile, Sequence, useCurrentFrame, interpolate, spring, useVideoConfig, Easing} from 'remotion';
import data from '../public/data.json';

const C = {
  bg: '#04060e', ink: '#eef3fb', dim: '#7d8798', ice: '#52a8ff', warm: '#f0b429',
  alert: '#ff5b4a', good: '#49d49d', line: '#232b3a',
};
const font = 'Inter, "Helvetica Neue", Arial, sans-serif';
const mono = '"SF Mono", Menlo, monospace';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const fade = (f, d) => interpolate(f, [0, 18, d - 18, d], [0, 1, 1, 0], clamp);
const ease = Easing.inOut(Easing.cubic);
const rnd = (i) => {const x = Math.sin(i * 912.73) * 10000; return x - Math.floor(x);};

const Stars = () => {
  const f = useCurrentFrame();
  const stars = React.useMemo(() => Array.from({length: 170}, (_, i) =>
    ({x: rnd(i) * 1920, y: rnd(i + 500) * 1080, s: 1 + (i % 3)})), []);
  return <AbsoluteFill style={{background: `radial-gradient(ellipse at 20% 100%, #0a1a33 0%, ${C.bg} 60%)`}}>
    {stars.map((s, i) => <div key={i} style={{position: 'absolute', left: s.x, top: s.y, width: s.s, height: s.s,
      borderRadius: 9, background: '#fff', opacity: 0.18 + 0.42 * Math.abs(Math.sin(f / 44 + i))}} />)}
  </AbsoluteFill>;
};

const Rise = ({children, delay = 0, y = 26}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 200}});
  return <div style={{opacity: s, transform: `translateY(${(1 - s) * y}px)`}}>{children}</div>;
};
const H1 = ({children, size = 62, color = C.ink, weight = 700}) =>
  <div style={{fontFamily: font, fontSize: size, fontWeight: weight, color, letterSpacing: -1.2, lineHeight: 1.15}}>{children}</div>;
const Sub = ({children, size = 30, color = C.dim}) =>
  <div style={{fontFamily: font, fontSize: size, fontWeight: 500, color, lineHeight: 1.35}}>{children}</div>;

const Earth = ({cx, cy, r}) => <>
  <circle cx={cx} cy={cy} r={r * 2.4} fill={C.ice} opacity="0.06" />
  <circle cx={cx} cy={cy} r={r} fill="#1b4f8c" />
  <circle cx={cx} cy={cy} r={r} fill="none" stroke={C.ice} strokeWidth="2" opacity="0.8" />
  <path d={`M ${cx - r} ${cy} A ${r} ${r * 0.45} 0 0 0 ${cx + r} ${cy}`} fill="none" stroke={C.ice} strokeWidth="1" opacity="0.35" />
</>;

// ---------------------------------------------------------------- 1. this week
const Week = ({d}) => {
  const f = useCurrentFrame();
  const n = data.week.count;
  const rocks = React.useMemo(() => Array.from({length: n}, (_, i) => ({
    a: rnd(i) * Math.PI * 2, r: 180 + rnd(i + 90) * 640, sp: 0.5 + rnd(i + 7) * 1.6,
    off: rnd(i + 31) * 300, s: 1.6 + rnd(i + 52) * 3.4,
  })), [n]);
  const shown = Math.round(interpolate(f, [20, 90], [0, n], clamp));
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080">
      <Earth cx={960} cy={560} r={74} />
      {rocks.slice(0, shown).map((k, i) => {
        const p = ((f * k.sp + k.off) % 300) / 300;
        const x = 960 + Math.cos(k.a) * (k.r * (1 - p) + 110 * p) * 1.5;
        const y = 560 + Math.sin(k.a) * (k.r * (1 - p) + 110 * p) * 0.8;
        return <g key={i} opacity={0.3 + 0.7 * Math.sin(Math.PI * p)}>
          <line x1={x} y1={y} x2={x + Math.cos(k.a) * 26} y2={y + Math.sin(k.a) * 14}
            stroke={C.warm} strokeWidth="1.2" opacity="0.5" />
          <circle cx={x} cy={y} r={k.s} fill={C.warm} />
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', top: 96, width: '100%', textAlign: 'center'}}>
      <Rise><H1 size={76}>{shown} asteroids pass Earth this week.</H1></Rise>
      <div style={{height: 20}} />
      <Rise delay={22}><Sub size={32}>{data.week.hazardous} of them are on NASA's potentially hazardous list. None of them will hit us.</Sub></Rise>
    </div>
    <div style={{position: 'absolute', bottom: 70, width: '100%', textAlign: 'center'}}>
      <Sub size={24}>NASA Near Earth Object Web Service · {data.span.start} to {data.span.end}</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 2. the whole year
const Year = ({d}) => {
  const f = useCurrentFrame();
  const shown = Math.round(interpolate(f, [25, 190], [0, data.total], {...clamp, easing: ease}));
  const months = data.by_month;
  const max = Math.max(...months.map((m) => m.count));
  const grown = interpolate(f, [60, 200], [0, 1], {...clamp, easing: ease});
  const label = (s) => {
    const [y, m] = s.split('-');
    return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m - 1] + ' ' + y.slice(2);
  };
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 84, width: '100%', textAlign: 'center'}}>
      <Rise><Sub size={32}>I asked for the whole next year</Sub></Rise>
      <div style={{height: 10}} />
      <div style={{fontFamily: font, fontSize: 168, fontWeight: 800, color: C.warm, letterSpacing: -6}}>
        {shown.toLocaleString('en-US')}
      </div>
      <Sub size={34}>scheduled close approaches · more than five a day</Sub>
    </div>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <line x1={250} y1={880} x2={1670} y2={880} stroke={C.line} strokeWidth="2" />
      {months.map((m, i) => {
        const w = (1420 / months.length) * 0.66;
        const x = 250 + (i + 0.5) * (1420 / months.length);
        const h = (m.count / max) * 230 * grown;
        return <g key={i}>
          <rect x={x - w / 2} y={880 - h} width={w} height={h} fill={C.ice} opacity="0.75" rx="3" />
          <text x={x} y={916} fill={C.dim} fontSize="19" fontFamily={font} textAnchor="middle">{label(m.month)}</text>
          <text x={x} y={880 - h - 12} fill={C.dim} fontSize="20" fontFamily={mono} textAnchor="middle"
            opacity={grown > 0.95 ? 1 : 0}>{m.count}</text>
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', bottom: 62, width: '100%', textAlign: 'center'}}>
      <Sub size={23}>close approaches per month · the first and last months are partial</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 3. the closest one
const Closest = ({d}) => {
  const f = useCurrentFrame();
  const a = data.closest;
  const p = interpolate(f, [30, 150], [0, 1], {...clamp, easing: ease});
  const MOON_R = 300;
  // the Moon sits to the right; the asteroid comes in on a different bearing so
  // the two are not drawn on top of each other at 1.01 lunar distances
  const BEAR = -1.05;
  const far = 1250, near = MOON_R * a.lunar_distances;
  const ar = far - (far - near) * p;
  const ax = 960 + Math.cos(BEAR) * ar, ay = 540 + Math.sin(BEAR) * ar;
  const card = interpolate(f, [150, 175], [0, 1], clamp);
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080">
      <circle cx={960} cy={540} r={MOON_R} fill="none" stroke={C.line} strokeWidth="2" strokeDasharray="6 10" />
      <Earth cx={960} cy={540} r={52} />
      <circle cx={960 + MOON_R} cy={540} r={14} fill="#9aa4b2" />
      <text x={960 + MOON_R} y={498} fill={C.dim} fontSize="22" fontFamily={font} textAnchor="middle">the Moon</text>
      <text x={960 + MOON_R} y={586} fill={C.dim} fontSize="19" fontFamily={mono} textAnchor="middle">384,400 km</text>
      <line x1={ax} y1={ay} x2={ax + Math.cos(BEAR) * 150} y2={ay + Math.sin(BEAR) * 150}
        stroke={C.alert} strokeWidth="2" opacity="0.45" />
      <circle cx={ax} cy={ay} r={11} fill={C.alert} />
      <circle cx={ax} cy={ay} r={26} fill={C.alert} opacity={0.18 * (1 - card)} />
      <text x={ax + 26} y={ay + 8} fill={C.alert} fontSize="24" fontFamily={font}
        opacity={card}>{a.lunar_distances} LD</text>
    </svg>
    <div style={{position: 'absolute', top: 86, left: 150}}>
      <Rise><H1 size={58}>The closest pass of the year</H1></Rise>
    </div>
    <div style={{position: 'absolute', bottom: 130, left: 150, opacity: card}}>
      <H1 size={52} color={C.alert}>{a.name}</H1>
      <div style={{height: 14}} />
      <Sub size={30}>{a.date} · {a.lunar_distances} lunar distances · {a.miss_km.toLocaleString('en-US')} km</Sub>
      <div style={{height: 6}} />
      <Sub size={30}>{a.speed_kmh.toLocaleString('en-US')} km/h</Sub>
    </div>
    <div style={{position: 'absolute', bottom: 130, right: 150, textAlign: 'right', opacity: card}}>
      <Sub size={26}>just outside the orbit of the Moon</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 4. how big
const Size = ({d}) => {
  const f = useCurrentFrame();
  const a = data.closest;
  const w = (m) => (m / 1600) * 1280;
  const lo = interpolate(f, [25, 70], [0, w(a.diameter_min_m)], {...clamp, easing: ease});
  const hi = interpolate(f, [60, 130], [0, w(a.diameter_max_m)], {...clamp, easing: ease});
  const refs = [['Eiffel Tower', 330], ['Burj Khalifa', 828]];
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 100, left: 170}}>
      <Rise><H1 size={58}>And it is not small.</H1></Rise>
      <div style={{height: 16}} />
      <Rise delay={16}><Sub size={32}>{a.name}, across</Sub></Rise>
    </div>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <rect x={320} y={470} width={hi} height={58} fill={C.warm} opacity="0.22" rx="4" />
      <rect x={320} y={470} width={lo} height={58} fill={C.warm} opacity="0.85" rx="4" />
      <line x1={320 + lo} y1={440} x2={320 + lo} y2={558} stroke={C.ink} strokeWidth="2" />
      <line x1={320 + hi} y1={440} x2={320 + hi} y2={558} stroke={C.ink} strokeWidth="2" opacity="0.6" />
      <text x={320 + lo} y={424} fill={C.ink} fontSize="30" fontFamily={mono} textAnchor="middle"
        opacity={lo > 10 ? 1 : 0}>{Math.round(a.diameter_min_m)} m</text>
      <text x={320 + hi} y={424} fill={C.ink} fontSize="30" fontFamily={mono} textAnchor="middle"
        opacity={hi > w(a.diameter_min_m) + 60 ? 0.75 : 0}>{Math.round(a.diameter_max_m)} m</text>
      {refs.map(([name, h], i) => {
        const x = 320 + w(h);
        return <g key={i} opacity={interpolate(f, [140 + i * 14, 165 + i * 14], [0, 0.7], clamp)}>
          <line x1={x} y1={600} x2={x} y2={660} stroke={C.dim} strokeWidth="1.5" strokeDasharray="4 6" />
          <text x={x} y={690} fill={C.dim} fontSize="22" fontFamily={font} textAnchor="middle">{name}</text>
          <text x={x} y={716} fill={C.dim} fontSize="19" fontFamily={mono} textAnchor="middle">{h} m</text>
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', bottom: 110, left: 170, opacity: interpolate(f, [200, 230], [0, 1], clamp)}}>
      <Sub size={30} color={C.ink}>Why a range of more than two to one? Because nobody has measured it.</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 5. the size ranges
const Ranges = ({d}) => {
  const f = useCurrentFrame();
  const rows = data.ranges;
  const X0 = 300, X1 = 1680, Y0 = 250, Y1 = 900;
  const lx = (m) => X0 + (Math.log10(Math.max(m, 0.5)) - Math.log10(0.5)) / (Math.log10(2000) - Math.log10(0.5)) * (X1 - X0);
  const n = Math.round(interpolate(f, [20, 180], [0, rows.length], {...clamp, easing: ease}));
  const ticks = [1, 10, 100, 1000];
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 76, left: 170}}>
      <Rise><H1 size={54}>Size comes from brightness, not a ruler.</H1></Rise>
      <div style={{height: 12}} />
      <Rise delay={16}><Sub size={30}>Each bar is one asteroid: NASA's minimum to maximum estimate.</Sub></Rise>
    </div>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      {ticks.map((v) => <g key={v}>
        <line x1={lx(v)} y1={Y0} x2={lx(v)} y2={Y1} stroke={C.line} strokeWidth="1.5" />
        <text x={lx(v)} y={Y1 + 36} fill={C.dim} fontSize="22" fontFamily={mono} textAnchor="middle">{v} m</text>
      </g>)}
      {rows.slice(0, n).map((r, i) => {
        const y = Y0 + (i + 0.5) * ((Y1 - Y0) / rows.length);
        return <g key={i}>
          <line x1={lx(r.lo)} y1={y} x2={lx(r.hi)} y2={y} stroke={C.ice} strokeWidth="5" opacity="0.8" strokeLinecap="round" />
          <circle cx={lx(r.lo)} cy={y} r="3.5" fill={C.ink} opacity="0.7" />
          <circle cx={lx(r.hi)} cy={y} r="3.5" fill={C.ink} opacity="0.7" />
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', bottom: 70, width: '100%', textAlign: 'center',
      opacity: interpolate(f, [220, 250], [0, 1], clamp)}}>
      <Sub size={32} color={C.warm}>The bar is how much we do not know.</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 6. the hazardous label
const Hazard = ({d}) => {
  const f = useCurrentFrame();
  const dots = data.total;
  const flagged = data.hazardous;
  const grid = React.useMemo(() => {
    const cols = 70, out = [];
    for (let i = 0; i < dots; i++) out.push({x: 300 + (i % cols) * 19, y: 276 + Math.floor(i / cols) * 16});
    return out;
  }, [dots]);
  const lit = interpolate(f, [60, 150], [0, 1], {...clamp, easing: ease});
  const counter = Math.round(interpolate(f, [60, 150], [0, flagged], clamp));
  const rule = interpolate(f, [200, 230], [0, 1], clamp);
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 84, left: 300}}>
      <Rise><H1 size={54}><span style={{color: C.alert}}>{counter}</span> of them are flagged “potentially hazardous”.</H1></Rise>
    </div>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      {grid.map((g, i) => {
        // mark exactly `flagged` of the dots, spread evenly through the grid
        const flag = Math.floor(i * flagged / dots) !== Math.floor((i + 1) * flagged / dots);
        return <circle key={i} cx={g.x} cy={g.y} r={flag ? 4.2 : 3}
          fill={flag ? C.alert : C.dim} opacity={flag ? 0.25 + 0.75 * lit : 0.3} />;
      })}
    </svg>
    <div style={{position: 'absolute', bottom: 96, left: 300, opacity: rule}}>
      <Sub size={30} color={C.ink}>The label means exactly two things:</Sub>
      <div style={{height: 14}} />
      <Sub size={28}>at least about 140 m across</Sub>
      <Sub size={28}>an orbit that comes within 7.5 million km of ours</Sub>
      <div style={{height: 18}} />
      <H1 size={40} color={C.warm}>It is a watch list. It is not a prediction.</H1>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 7. the honest part
const Honest = ({d}) => {
  const f = useCurrentFrame();
  const X0 = 300, X1 = 1660, Y = 560;
  const lx = (ld) => X0 + (Math.log10(ld) - 0) / (Math.log10(200) - 0) * (X1 - X0);
  const n = Math.round(interpolate(f, [20, 140], [0, data.scatter.length], {...clamp, easing: ease}));
  const moon = interpolate(f, [150, 180], [0, 1], clamp);
  const text = interpolate(f, [230, 260], [0, 1], clamp);
  const ticks = [1, 10, 100];
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 86, left: 300}}>
      <Rise><H1 size={54}>Not one of the {data.total.toLocaleString('en-US')} comes closer than the Moon.</H1></Rise>
    </div>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <line x1={X0} y1={Y + 190} x2={X1} y2={Y + 190} stroke={C.line} strokeWidth="2" />
      {ticks.map((v) => <text key={v} x={lx(v)} y={Y + 232} fill={C.dim} fontSize="22" fontFamily={mono}
        textAnchor="middle">{v} LD</text>)}
      {data.scatter.slice(0, n).map((s, i) => {
        const y = Y + (rnd(i + 3000) - 0.5) * 310;
        return <circle key={i} cx={lx(Math.max(s.ld, 1))} cy={y} r={s.h ? 3.6 : 2.6}
          fill={s.h ? C.alert : C.ice} opacity="0.6" />;
      })}
      <line x1={lx(1)} y1={Y - 210} x2={lx(1)} y2={Y + 190} stroke="#9aa4b2" strokeWidth="2" opacity={moon} />
      <text x={lx(1) + 16} y={Y - 180} fill="#9aa4b2" fontSize="26" fontFamily={font} opacity={moon}>the Moon's orbit</text>
    </svg>
    <div style={{position: 'absolute', bottom: 84, left: 300, opacity: text, maxWidth: 1360}}>
      <Sub size={34} color={C.ink}>Not because nothing will. The ones that pass that close are small,
        and we usually find them a few days before they arrive.</Sub>
      <div style={{height: 16}} />
      <H1 size={40} color={C.warm}>The calendar is only as good as the catalogue.</H1>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 8. end card
const End = ({d}) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{opacity: fade(f, d), alignItems: 'center', justifyContent: 'center'}}>
    <Rise><H1 size={76}>Asteroid tracker</H1></Rise>
    <div style={{height: 22}} />
    <Rise delay={16}><Sub size={34}>Live close approaches from NASA's Near Earth Object Web Service</Sub></Rise>
    <div style={{height: 54}} />
    <Rise delay={30}>
      <div style={{display: 'flex', gap: 80}}>
        {[[data.total.toLocaleString('en-US'), 'approaches in a year'],
          [data.hazardous, 'flagged'],
          [data.closest.lunar_distances, 'closest, in lunar distances']].map(([v, k], i) =>
          <div key={i} style={{textAlign: 'center'}}>
            <div style={{fontFamily: font, fontSize: 72, fontWeight: 800, color: C.warm, letterSpacing: -2}}>{v}</div>
            <Sub size={24}>{k}</Sub>
          </div>)}
      </div>
    </Rise>
    <div style={{height: 70}} />
    <Rise delay={46}><Sub size={28} color={C.ice}>github.com/cloudynirvana/asteroid-tracker</Sub></Rise>
    <div style={{height: 14}} />
    <Rise delay={54}><Sub size={22}>data pulled {data.generated} · api.nasa.gov</Sub></Rise>
  </AbsoluteFill>;
};

// ----------------------------------------------------------------
const SCENES = [[Week, 270], [Year, 345], [Closest, 405], [Size, 360],
                [Ranges, 450], [Hazard, 510], [Honest, 480], [End, 315]];

export const Film = () => {
  let at = 0;
  return <AbsoluteFill style={{background: C.bg}}>
    <Stars />
    <Audio src={staticFile('soundtrack.wav')} />
    {SCENES.map(([Comp, d], i) => {
      const from = at; at += d;
      return <Sequence key={i} from={from} durationInFrames={d}><Comp d={d} /></Sequence>;
    })}
  </AbsoluteFill>;
};
