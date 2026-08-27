import React from "react";

const HAND_CONN: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [0, 9], [9, 10], [10, 11], [11, 12],
  [0, 13], [13, 14], [14, 15], [15, 16],
  [0, 17], [17, 18], [18, 19], [19, 20],
  [5, 9], [9, 13], [13, 17],
];

// Upper-body subset of MediaPipe Pose's connection graph -- indices match
// the standard 33-point Pose landmark model (11/12 shoulders, 13/14 elbows,
// 15/16 wrists, 23/24 hips).
const POSE_CONN: [number, number][] = [
  [11, 12],
  [11, 13], [13, 15],
  [12, 14], [14, 16],
  [11, 23], [12, 24],
  [23, 24],
];

type Landmarks = {
  left_hand: [number, number][];
  right_hand: [number, number][];
  pose: [number, number][];
};

type Props = {
  landmarks: Landmarks | null | undefined;
  confidence: number;
};

const W = 640;
const H = 480;

function toPixels(points: [number, number][]): [number, number][] {
  return points.map(([x, y]) => [x * W, y * H]);
}

// A hand slot MediaPipe didn't detect comes back all-zero (see
// extract_single_video.py's zero-fill), so treat an all-(0,0) group as
// "not present" rather than drawing a hand collapsed at the origin.
function isPresent(points: [number, number][]): boolean {
  return points.some(([x, y]) => x !== 0 || y !== 0);
}

function Skeleton({
  points,
  connections,
  color,
  jointRadius = 4,
}: {
  points: [number, number][];
  connections: [number, number][];
  color: string;
  jointRadius?: number;
}) {
  return (
    <>
      {connections.map(([a, b], i) => (
        <line
          key={`bone-${a}-${b}-${i}`}
          x1={points[a][0]}
          y1={points[a][1]}
          x2={points[b][0]}
          y2={points[b][1]}
          stroke={color}
          strokeWidth={3}
          opacity={0.8}
        />
      ))}

      {points.map(([x, y], i) => (
        <circle
          key={`point-${i}`}
          cx={x}
          cy={y}
          r={i === 0 ? jointRadius + 3 : jointRadius}
          fill={color}
          opacity={0.95}
        />
      ))}
    </>
  );
}

export default function CameraOverlay({ landmarks, confidence }: Props) {
  const leftHandRaw = landmarks?.left_hand ?? [];
  const rightHandRaw = landmarks?.right_hand ?? [];
  const poseRaw = landmarks?.pose ?? [];

  const hasLeft = isPresent(leftHandRaw);
  const hasRight = isPresent(rightHandRaw);

  // No hand detected at all -- nothing useful to draw.
  if (!landmarks || (!hasLeft && !hasRight)) {
    return null;
  }

  const leftHand = hasLeft ? toPixels(leftHandRaw) : null;
  const rightHand = hasRight ? toPixels(rightHandRaw) : null;
  const pose = isPresent(poseRaw) ? toPixels(poseRaw) : null;

  // Bounding box tracks whichever hand(s) are actually present. Pose points
  // are deliberately excluded so the box hugs the hand(s) being signed
  // instead of the whole upper body.
  const handPoints = [...(leftHand ?? []), ...(rightHand ?? [])];

  const padding = 30;

  const xs = handPoints.map((p) => p[0]);
  const ys = handPoints.map((p) => p[1]);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const bx = minX - padding;
  const by = minY - padding;
  const bw = maxX - minX + padding * 2;
  const bh = maxY - minY + padding * 2;

  const color = confidence >= 0.65 ? "#6C47FF" : "#F59E0B";

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full">
      {/* dark transparent overlay */}
      <rect width={W} height={H} fill="rgba(10,8,32,0.15)" />

      {/* grid */}
      {Array.from({ length: 6 }).map((_, i) => (
        <line
          key={"h" + i}
          x1={0}
          y1={((i + 1) * H) / 7}
          x2={W}
          y2={((i + 1) * H) / 7}
          stroke="white"
          strokeWidth="0.5"
          opacity="0.12"
        />
      ))}

      {Array.from({ length: 8 }).map((_, i) => (
        <line
          key={"v" + i}
          x1={((i + 1) * W) / 9}
          y1={0}
          x2={((i + 1) * W) / 9}
          y2={H}
          stroke="white"
          strokeWidth="0.5"
          opacity="0.12"
        />
      ))}

      {/* pose, drawn first / lighter so it doesn't visually compete with the hands */}
      {pose && (
        <Skeleton
          points={pose}
          connections={POSE_CONN}
          color="rgba(255,255,255,0.45)"
          jointRadius={3}
        />
      )}

      {/* both hands, drawn independently */}
      {leftHand && <Skeleton points={leftHand} connections={HAND_CONN} color={color} />}
      {rightHand && <Skeleton points={rightHand} connections={HAND_CONN} color={color} />}

      {/* bounding box around the detected hand(s) */}
      {handPoints.length > 0 && (
        <>
          <rect
            x={bx}
            y={by}
            width={bw}
            height={bh}
            rx={12}
            fill="none"
            stroke={color}
            strokeWidth={2}
            strokeDasharray="10 6"
            opacity={0.7}
          />

          {[
            [bx, by, 1, 1],
            [bx + bw, by, -1, 1],
            [bx, by + bh, 1, -1],
            [bx + bw, by + bh, -1, -1],
          ].map(([cx, cy, dx, dy], i) => (
            <g key={i}>
              <line x1={cx} y1={cy} x2={cx + dx * 18} y2={cy} stroke={color} strokeWidth={4} />
              <line x1={cx} y1={cy} x2={cx} y2={cy + dy * 18} stroke={color} strokeWidth={4} />
            </g>
          ))}
        </>
      )}

      {/* live badge */}
      <rect x="12" y="12" width="60" height="24" rx="7" fill="#EF4444" />
      <circle cx="24" cy="24" r="4" fill="white" />
      <text x="34" y="28" fill="white" fontSize="12" fontWeight="bold">
        LIVE
      </text>
    </svg>
  );
}