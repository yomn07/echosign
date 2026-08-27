import {
  useEffect,
  useRef,
  useState,
} from "react";

type Point3D = [
  number,
  number,
  number
];

type Frame = {
  left_hand: Point3D[];
  right_hand: Point3D[];
  pose: Point3D[];
  face: Point3D[];
};

/* =========================
   HAND
========================= */

const HAND_CONNECTIONS = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],

  [0, 5],
  [5, 6],
  [6, 7],
  [7, 8],

  [5, 9],
  [9, 10],
  [10, 11],
  [11, 12],

  [9, 13],
  [13, 14],
  [14, 15],
  [15, 16],

  [13, 17],
  [17, 18],
  [18, 19],
  [19, 20],

  [0, 17],
];

/* =========================
   POSE
========================= */

const POSE_CONNECTIONS = [
  [11, 13],
  [13, 15],

  [12, 14],
  [14, 16],

  [11, 12],

  [11, 23],
  [12, 24],

  [23, 24],

  [23, 25],
  [25, 27],

  [24, 26],
  [26, 28],
];

/* =========================
   FACE OUTER MESH
========================= */

const FACE_CONNECTIONS = [
  [10, 338],
  [338, 297],
  [297, 332],
  [332, 284],
  [284, 251],
  [251, 389],
  [389, 356],
  [356, 454],
  [454, 323],
  [323, 361],
  [361, 288],
  [288, 397],
  [397, 365],
  [365, 379],
  [379, 378],
  [378, 400],
  [400, 377],
  [377, 152],
  [152, 148],
  [148, 176],
  [176, 149],
  [149, 150],
  [150, 136],
  [136, 172],
  [172, 58],
  [58, 132],
  [132, 93],
  [93, 234],
  [234, 127],
  [127, 162],
  [162, 21],
  [21, 54],
  [54, 103],
  [103, 67],
  [67, 109],
  [109, 10],
];

/* =========================
   FACE DETAILS
========================= */

const FACE_DETAIL_CONNECTIONS = [
  // Left eye
  [33, 133],
  [133, 160],
  [160, 159],
  [159, 158],
  [158, 157],
  [157, 173],

  // Right eye
  [362, 263],
  [263, 387],
  [387, 386],
  [386, 385],
  [385, 384],
  [384, 398],

  // Mouth
  [61, 291],
  [291, 308],
  [308, 324],
  [324, 318],
  [318, 78],
  [78, 95],
  [95, 88],
  [88, 61],

  // Nose
  [1, 2],
  [2, 98],
  [98, 327],
  [327, 168],
  [168, 6],
];

/* =========================
   DRAW POINT
========================= */
function drawNeck(
  ctx: CanvasRenderingContext2D,
  pose: Point3D[],
  face: Point3D[],
  w: number,
  h: number
) {
  const leftShoulder = pose[11];
  const rightShoulder = pose[12];

  if (!leftShoulder || !rightShoulder) return;

  const shoulderX =
    (leftShoulder[0] + rightShoulder[0]) / 2;

  const shoulderY =
    (leftShoulder[1] + rightShoulder[1]) / 2;

  /*
   * Use the chin landmark from Face Mesh
   * to determine where the neck should reach.
   */
  const chin = face[152];

  if (!chin) return;

  const neckBottomY = shoulderY;

  const neckTopY =
    chin[1] +
    (shoulderY - chin[1]) * 0.30;

  const neckWidth =
    Math.abs(
      leftShoulder[0] -
      rightShoulder[0]
    ) * 0.18;

  const leftX =
    shoulderX - neckWidth;

  const rightX =
    shoulderX + neckWidth;

  ctx.save();

  ctx.strokeStyle = "#00e5ff";
  ctx.lineWidth = 5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  ctx.shadowColor =
    "rgba(0,229,255,0.7)";

  ctx.shadowBlur = 8;

  /*
   * Left side of neck
   */
  ctx.beginPath();

  ctx.moveTo(
    leftX * w,
    neckTopY * h
  );

  ctx.lineTo(
    leftX * w,
    neckBottomY * h
  );

  ctx.stroke();

  /*
   * Right side of neck
   */
  ctx.beginPath();

  ctx.moveTo(
    rightX * w,
    neckTopY * h
  );

  ctx.lineTo(
    rightX * w,
    neckBottomY * h
  );

  ctx.stroke();

  /*
   * Connect neck to shoulders
   */
  ctx.beginPath();

  ctx.moveTo(
    leftX * w,
    neckBottomY * h
  );

  ctx.lineTo(
    leftShoulder[0] * w,
    leftShoulder[1] * h
  );

  ctx.moveTo(
    rightX * w,
    neckBottomY * h
  );

  ctx.lineTo(
    rightShoulder[0] * w,
    rightShoulder[1] * h
  );

  ctx.stroke();

  ctx.restore();
}
function drawPoint(
  ctx: CanvasRenderingContext2D,
  p: Point3D,
  w: number,
  h: number,
  color: string,
  size = 4
) {
  const x = p[0] * w;
  const y = p[1] * h;

  ctx.fillStyle = color;

  ctx.beginPath();

  ctx.arc(
    x,
    y,
    size,
    0,
    Math.PI * 2
  );

  ctx.fill();
}

/* =========================
   DRAW CONNECTIONS
========================= */

function drawLines(
  ctx: CanvasRenderingContext2D,
  points: Point3D[],
  connections: number[],
  w: number,
  h: number,
  color: string,
  width = 3
) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  for (
    let i = 0;
    i < connections.length;
    i += 2
  ) {
    const a = points[connections[i]];
    const b = points[connections[i + 1]];

    if (!a || !b) continue;

    ctx.beginPath();

    ctx.moveTo(
      a[0] * w,
      a[1] * h
    );

    ctx.lineTo(
      b[0] * w,
      b[1] * h
    );

    ctx.stroke();
  }
}

/* =========================
   SMOOTH FACE CONTOUR
========================= */

function drawFaceContour(
  ctx: CanvasRenderingContext2D,
  face: Point3D[],
  w: number,
  h: number
) {
  if (face.length < 400) return;

  /*
   * Main face boundary.
   * These landmarks create a much cleaner
   * head silhouette.
   */
  const contour = [
    10,
    338,
    297,
    332,
    284,
    251,
    389,
    356,
    454,
    323,
    361,
    288,
    397,
    365,
    379,
    378,
    400,
    377,
    152,
    148,
    176,
    149,
    150,
    136,
    172,
    58,
    132,
    93,
    234,
    127,
    162,
    21,
    54,
    103,
    67,
    109,
  ];

  const points = contour
    .map((id) => face[id])
    .filter(Boolean);

  if (points.length < 3) return;

  /*
   * Draw a smooth quadratic curve
   * through the face boundary.
   */
  ctx.beginPath();

  const first = points[0];

  ctx.moveTo(
    first[0] * w,
    first[1] * h
  );

  for (let i = 1; i < points.length; i++) {
    const current = points[i];
    const next =
      points[(i + 1) % points.length];

    const cx = current[0] * w;
    const cy = current[1] * h;

    const nx = next[0] * w;
    const ny = next[1] * h;

    const midX = (cx + nx) / 2;
    const midY = (cy + ny) / 2;

    ctx.quadraticCurveTo(
      cx,
      cy,
      midX,
      midY
    );
  }

  ctx.closePath();

  ctx.strokeStyle =
    "rgba(255, 220, 180, 0.95)";

  ctx.lineWidth = 5;

  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  ctx.stroke();
}

/* =========================
   FACE GLOW
========================= */

function drawFaceGlow(
  ctx: CanvasRenderingContext2D,
  face: Point3D[],
  w: number,
  h: number
) {
  if (!face.length) return;

  ctx.save();

  ctx.shadowColor =
    "rgba(255, 80, 160, 0.7)";

  ctx.shadowBlur = 8;

  drawLines(
    ctx,
    face,
    FACE_CONNECTIONS.flat(),
    w,
    h,
    "rgba(255, 120, 180, 0.85)",
    2
  );

  ctx.restore();
}

/* =========================
   COMPONENT
========================= */

export default function LandmarkPlayer({
  word,
  playing,
}: {
  word: string;
  playing: boolean;
}) {
  const canvas =
    useRef<HTMLCanvasElement | null>(null);

  const [frames, setFrames] =
    useState<Frame[]>([]);

  const current =
    useRef(0);

  /* =========================
     LOAD LANDMARK DATA
  ========================= */

  useEffect(() => {
    current.current = 0;

    fetch(
      `http://localhost:8000/landmark/${word}`
    )
      .then((r) => r.json())
      .then((data) => {
        setFrames(data.frames || []);
      })
      .catch((error) => {
        console.error(
          "Failed to load landmarks:",
          error
        );
      });
  }, [word]);

  /* =========================
     ANIMATION
  ========================= */

  useEffect(() => {
    if (!playing || frames.length === 0) {
      return;
    }

    const timer = setInterval(() => {
      const canvasElement = canvas.current;

      if (!canvasElement) return;

      const ctx =
        canvasElement.getContext("2d");

      if (!ctx) return;

      const frame =
        frames[current.current];

      if (!frame) return;

      const w = canvasElement.width;
      const h = canvasElement.height;

      /* Clear */
      ctx.clearRect(
        0,
        0,
        w,
        h
      );

      /*
       * Better rendering quality
       */
      ctx.imageSmoothingEnabled = true;

      /* =========================
         FACE
      ========================= */

      if (frame.face?.length) {
        drawFaceGlow(
          ctx,
          frame.face,
          w,
          h
        );

        drawLines(
          ctx,
          frame.face,
          FACE_DETAIL_CONNECTIONS.flat(),
          w,
          h,
          "#ff79b0",
          2
        );

        drawFaceContour(
          ctx,
          frame.face,
          w,
          h
        );
      }

      /* =========================
         POSE
      ========================= */

      if (frame.pose?.length) {
        ctx.save();

        ctx.shadowColor =
          "rgba(0, 229, 255, 0.7)";

        ctx.shadowBlur = 8;

        drawLines(
          ctx,
          frame.pose,
          POSE_CONNECTIONS.flat(),
          w,
          h,
          "#00e5ff",
          5
        );

        ctx.restore();

        frame.pose.forEach((p) =>
          drawPoint(
            ctx,
            p,
            w,
            h,
            "#8ff8ff",
            5
          )
        );
      }

      /* =========================
         LEFT HAND
      ========================= */

      if (frame.left_hand?.length) {
        ctx.save();

        ctx.shadowColor =
          "rgba(0, 255, 136, 0.7)";

        ctx.shadowBlur = 8;

        drawLines(
          ctx,
          frame.left_hand,
          HAND_CONNECTIONS.flat(),
          w,
          h,
          "#00ff88",
          4
        );

        ctx.restore();

        frame.left_hand.forEach((p) =>
          drawPoint(
            ctx,
            p,
            w,
            h,
            "#8affc7",
            4
          )
        );
      }

      /* =========================
         RIGHT HAND
      ========================= */

      if (frame.right_hand?.length) {
        ctx.save();

        ctx.shadowColor =
          "rgba(255, 170, 0, 0.7)";

        ctx.shadowBlur = 8;

        drawLines(
          ctx,
          frame.right_hand,
          HAND_CONNECTIONS.flat(),
          w,
          h,
          "#ffaa00",
          4
        );

        ctx.restore();

        frame.right_hand.forEach((p) =>
          drawPoint(
            ctx,
            p,
            w,
            h,
            "#ffd166",
            4
          )
        );
      }

      /* =========================
         FACE POINTS
      ========================= */

      if (frame.face?.length) {
        frame.face.forEach((p) =>
          drawPoint(
            ctx,
            p,
            w,
            h,
            "rgba(255, 150, 200, 0.75)",
            1.4
          )
        );
      }

      /* =========================
         NEXT FRAME
      ========================= */

      current.current++;

      if (
        current.current >=
        frames.length
      ) {
        current.current = 0;
      }
    }, 33);

    return () => {
      clearInterval(timer);
    };
  }, [playing, frames]);

  /* =========================
     CANVAS
  ========================= */

  return (
    <canvas
      ref={canvas}
      width={500}
      height={700}
      style={{
        width: "100%",
        height: "100%",
        display: "block",
        background:
          "#020523",
      }}
    />
  );
}

