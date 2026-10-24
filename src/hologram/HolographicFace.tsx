import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { AssistantState } from '../types/assistant';

interface HolographicFaceProps {
  state: AssistantState;
  waveformLevel: number;
  lowPowerMode?: boolean;
  minimal?: boolean;
}

// Build human anatomical facial topology matching the reference video
function createAnatomicalFaceGeometry() {
  // Symmetrical landmarks: [x, y, z]
  // Centerline:
  const centerPoints: [number, number, number][] = [
    [0.0, 1.18, 0.25],   // 0: Top hairline center
    [0.0, 0.92, 0.48],   // 1: Upper forehead
    [0.0, 0.68, 0.66],   // 2: Mid forehead
    [0.0, 0.44, 0.78],   // 3: Glabella (between eyes)
    [0.0, 0.24, 0.92],   // 4: Nose bridge top
    [0.0, 0.02, 1.06],   // 5: Nose bridge mid
    [0.0, -0.12, 1.22],  // 6: Nose tip
    [0.0, -0.26, 0.94],  // 7: Subnasale (under nose)
    [0.0, -0.38, 0.98],  // 8: Upper lip top
    [0.0, -0.46, 0.90],  // 9: Mouth center / opening
    [0.0, -0.56, 0.96],  // 10: Lower lip bottom
    [0.0, -0.72, 0.82],  // 11: Chin groove
    [0.0, -0.92, 0.88],  // 12: Chin apex
    [0.0, -1.14, 0.50],  // 13: Jaw bottom
  ];

  // Right side landmarks (x > 0), left side will be mirrored (x < 0)
  const halfPoints: [number, number, number][] = [
    // Forehead & Temple:
    [0.32, 1.10, 0.22],   // 0 (index 14): Hairline mid
    [0.64, 0.96, 0.12],   // 1 (index 15): Temple top
    [0.82, 0.68, -0.05],  // 2 (index 16): Temple outer
    [0.30, 0.88, 0.44],   // 3 (index 17): Forehead inner
    [0.58, 0.80, 0.32],   // 4 (index 18): Forehead mid-outer
    [0.26, 0.62, 0.62],   // 5 (index 19): Brow inner-upper
    [0.54, 0.56, 0.50],   // 6 (index 20): Brow mid-upper
    [0.78, 0.46, 0.18],   // 7 (index 21): Temple mid

    // Eyebrow arch:
    [0.18, 0.42, 0.78],   // 8 (index 22): Brow inner
    [0.42, 0.44, 0.72],   // 9 (index 23): Brow arch peak
    [0.64, 0.36, 0.48],   // 10 (index 24): Brow tail

    // Eye contour:
    [0.16, 0.28, 0.74],   // 11 (index 25): Eye inner corner
    [0.36, 0.34, 0.76],   // 12 (index 26): Upper eyelid peak
    [0.56, 0.26, 0.60],   // 13 (index 27): Eye outer corner
    [0.36, 0.20, 0.70],   // 14 (index 28): Lower eyelid bottom
    [0.36, 0.27, 0.73],   // 15 (index 29): Eye pupil center

    // Cheek & Nose:
    [0.16, 0.08, 0.88],   // 16 (index 30): Nose side mid
    [0.22, -0.12, 0.98],  // 17 (index 31): Nostril wing
    [0.44, 0.08, 0.68],   // 18 (index 32): Inner cheekbone
    [0.72, 0.12, 0.36],   // 19 (index 33): Outer cheekbone apex
    [0.88, 0.18, 0.05],   // 20 (index 34): Zygomatic arch outer

    // Mid cheek & Nasolabial:
    [0.20, -0.28, 0.82],  // 21 (index 35): Nasolabial groove
    [0.46, -0.16, 0.60],  // 22 (index 36): Mid cheek
    [0.70, -0.12, 0.26],  // 23 (index 37): Cheek outer

    // Mouth:
    [0.18, -0.37, 0.90],  // 24 (index 38): Upper lip peak (philtrum ridge)
    [0.34, -0.45, 0.78],  // 25 (index 39): Mouth corner
    [0.16, -0.54, 0.88],  // 26 (index 40): Lower lip mid-bottom

    // Jawline & Chin:
    [0.24, -0.70, 0.76],  // 27 (index 41): Chin side
    [0.48, -0.50, 0.52],  // 28 (index 42): Lower cheek / jaw inner
    [0.72, -0.42, 0.18],  // 29 (index 43): Jaw corner (mandible angle)
    [0.20, -0.90, 0.78],  // 30 (index 44): Chin apex side
    [0.44, -0.78, 0.48],  // 31 (index 45): Jaw lower edge mid
    [0.16, -1.10, 0.46],  // 32 (index 46): Jaw bottom side
  ];

  const totalCenter = centerPoints.length; // 14
  const totalHalf = halfPoints.length;     // 33

  // Assemble full vertex array:
  // indices 0..13: Center points
  // indices 14..46: Right side points (x > 0)
  // indices 47..79: Left side points (mirrored, x < 0)
  const allVertices: number[] = [];

  // 1. Center vertices
  for (const p of centerPoints) {
    allVertices.push(p[0], p[1], p[2]);
  }
  // 2. Right side vertices
  for (const p of halfPoints) {
    allVertices.push(p[0], p[1], p[2]);
  }
  // 3. Left side vertices (mirrored x)
  for (const p of halfPoints) {
    allVertices.push(-p[0], p[1], p[2]);
  }

  // Triangles construction
  const indices: number[] = [];

  // Helper to add symmetrical triangle
  // rA, rB, rC are indices for center or right side.
  // If index >= 14, left counterpart is index + 33.
  const getLeft = (idx: number) => (idx >= totalCenter ? idx + totalHalf : idx);

  const addTri = (a: number, b: number, c: number) => {
    // Right side triangle
    indices.push(a, b, c);
    // Mirrored left side triangle (reverse winding for correct front normal)
    indices.push(getLeft(a), getLeft(c), getLeft(b));
  };

  // Forehead triangles
  addTri(0, 1, 14);
  addTri(1, 17, 14);
  addTri(14, 17, 15);
  addTri(15, 17, 18);
  addTri(15, 18, 16);
  addTri(1, 2, 17);
  addTri(2, 19, 17);
  addTri(17, 19, 20);
  addTri(17, 20, 18);
  addTri(18, 20, 21);
  addTri(16, 18, 21);

  // Brow and Glabella
  addTri(2, 3, 19);
  addTri(3, 22, 19);
  addTri(19, 22, 23);
  addTri(19, 23, 20);
  addTri(20, 23, 24);
  addTri(20, 24, 21);

  // Eye Area
  addTri(3, 4, 25);
  addTri(3, 25, 22);
  addTri(22, 25, 26);
  addTri(22, 26, 23);
  addTri(23, 26, 27);
  addTri(23, 27, 24);
  addTri(24, 27, 21);
  addTri(21, 27, 34);

  // Eye socket lower / cheek upper
  addTri(4, 30, 25);
  addTri(25, 30, 28);
  addTri(25, 28, 26);
  addTri(26, 28, 27);
  addTri(27, 28, 32);
  addTri(27, 32, 33);
  addTri(27, 33, 34);

  // Nose
  addTri(4, 5, 30);
  addTri(5, 6, 31);
  addTri(5, 31, 30);
  addTri(6, 7, 31);
  addTri(7, 35, 31);
  addTri(30, 31, 32);
  addTri(31, 35, 36);
  addTri(31, 36, 32);

  // Cheek & Zygomatic
  addTri(28, 30, 32);
  addTri(32, 36, 33);
  addTri(33, 36, 37);
  addTri(33, 37, 34);
  addTri(34, 37, 43);

  // Mouth area & Lips
  addTri(7, 8, 35);
  addTri(8, 38, 35);
  addTri(35, 38, 39);
  addTri(35, 39, 36);
  addTri(8, 9, 38);
  addTri(9, 39, 38);
  addTri(9, 10, 40);
  addTri(9, 40, 39);
  addTri(10, 11, 40);
  addTri(40, 11, 41);
  addTri(40, 41, 39);
  addTri(36, 39, 42);
  addTri(36, 42, 37);
  addTri(37, 42, 43);

  // Chin & Jawline
  addTri(11, 12, 41);
  addTri(41, 12, 44);
  addTri(41, 44, 42);
  addTri(42, 44, 45);
  addTri(42, 45, 43);
  addTri(12, 13, 44);
  addTri(44, 13, 46);
  addTri(44, 46, 45);

  const geo = new THREE.BufferGeometry();
  const posArr = new Float32Array(allVertices);
  geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();

  // Create wireframe geometry from the anatomical face mesh
  const wireGeo = new THREE.WireframeGeometry(geo);

  // Pupil points
  const pupilGeo = new THREE.BufferGeometry();
  // Index 29 is right pupil, 29+33=62 is left pupil
  const pupilPos = new Float32Array([
    allVertices[29 * 3], allVertices[29 * 3 + 1], allVertices[29 * 3 + 2] + 0.04,
    allVertices[62 * 3], allVertices[62 * 3 + 1], allVertices[62 * 3 + 2] + 0.04,
  ]);
  pupilGeo.setAttribute('position', new THREE.BufferAttribute(pupilPos, 3));

  return {
    geometry: geo,
    wireframeGeometry: wireGeo,
    pupilGeometry: pupilGeo,
    initialVertices: posArr.slice(),
  };
}

// Procedural 3D Holographic AI Face matching video
const ReferenceHolographicFace: React.FC<{
  state: AssistantState;
  waveformLevel: number;
}> = ({ state, waveformLevel }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const wireframeRef = useRef<THREE.LineSegments>(null);
  const nodesRef = useRef<THREE.Points>(null);
  const pupilsRef = useRef<THREE.Group>(null);
  const auraRef = useRef<THREE.Mesh>(null);

  const { geometry, wireframeGeometry, initialVertices, wireIndices } = useMemo(() => {
    const face = createAnatomicalFaceGeometry();
    const source = face.geometry.getAttribute('position');
    const lines = face.wireframeGeometry.getAttribute('position');
    const key = (x: number, y: number, z: number) => `${x.toFixed(5)},${y.toFixed(5)},${z.toFixed(5)}`;
    const lookup = new Map<string, number>();
    for (let i = 0; i < source.count; i++) lookup.set(key(source.getX(i), source.getY(i), source.getZ(i)), i);
    const indices = Array.from({ length: lines.count }, (_, i) => lookup.get(key(lines.getX(i), lines.getY(i), lines.getZ(i))) ?? -1);
    return { ...face, wireIndices: indices };
  }, []);

  // Node particle texture for glowing vertex dots
  const nodeTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext('2d')!;
    const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 30);
    grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
    grad.addColorStop(0.3, 'rgba(0, 229, 229, 0.9)');
    grad.addColorStop(0.7, 'rgba(0, 229, 229, 0.3)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(canvas);
  }, []);

  // Pupil ring texture
  const pupilTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d')!;
    ctx.strokeStyle = '#00FFFF';
    ctx.lineWidth = 6;
    ctx.shadowColor = '#00FFFF';
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(64, 64, 40, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(64, 64, 18, 0, Math.PI * 2);
    ctx.fill();
    return new THREE.CanvasTexture(canvas);
  }, []);

  // Aura background texture (radial cyan glow behind face)
  const auraTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d')!;
    const grad = ctx.createRadialGradient(128, 128, 20, 128, 128, 120);
    grad.addColorStop(0, 'rgba(0, 229, 229, 0.22)');
    grad.addColorStop(0.5, 'rgba(0, 200, 229, 0.08)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);
    return new THREE.CanvasTexture(canvas);
  }, []);

  useFrame((rState) => {
    const t = rState.clock.getElapsedTime();

    // 1. Organic breathing and slow 3D head perspective movement
    const breathing = Math.sin(t * 1.8) * 0.035;
    const waveDisplacement = (state === 'LISTENING' || state === 'SPEAKING') ? waveformLevel * 0.08 : 0;
    const headRotX = Math.sin(t * 0.7) * 0.04 + (state === 'THINKING' ? Math.sin(t * 2) * 0.06 : 0);
    const headRotY = Math.cos(t * 0.5) * 0.07;

    if (meshRef.current && wireframeRef.current && nodesRef.current) {
      meshRef.current.position.y = breathing + waveDisplacement;
      meshRef.current.rotation.x = headRotX;
      meshRef.current.rotation.y = headRotY;

      wireframeRef.current.position.y = breathing + waveDisplacement;
      wireframeRef.current.rotation.x = headRotX;
      wireframeRef.current.rotation.y = headRotY;

      nodesRef.current.position.y = breathing + waveDisplacement;
      nodesRef.current.rotation.x = headRotX;
      nodesRef.current.rotation.y = headRotY;

      if (pupilsRef.current) {
        pupilsRef.current.position.y = breathing + waveDisplacement;
        pupilsRef.current.rotation.x = headRotX;
        pupilsRef.current.rotation.y = headRotY;
      }

      // 2. Anatomical Mouth movement when SPEAKING (Jaw drops & lips open)
      const posAttr = geometry.attributes.position;
      const count = posAttr.count;

      if (state === 'SPEAKING' || state === 'LISTENING') {
        for (let i = 0; i < count; i++) {
          const initX = initialVertices[i * 3];
          const initY = initialVertices[i * 3 + 1];
          const initZ = initialVertices[i * 3 + 2];

          let dispY = 0;
          let dispZ = 0;

          // Mouth & Jaw vertices move with speech
          if (state === 'SPEAKING') {
            // Lower lip and jaw indices: 9, 10, 11, 12, 13 and lower cheeks
            if (initY < -0.38) {
              const speechFactor = (Math.sin(t * 15) * 0.5 + 0.5) * (0.06 + waveformLevel * 0.12);
              dispY = -speechFactor;
              dispZ = speechFactor * 0.2;
            }
          }

          // Listening ripple across brow and cheeks
          if (state === 'LISTENING') {
            const ripple = Math.sin(t * 8 + initX * 4) * (waveformLevel * 0.03);
            dispZ = ripple;
          }

          posAttr.setXYZ(i, initX, initY + dispY, initZ + dispZ);
        }
        // R3F updates this Three.js buffer inside useFrame, outside React rendering.
        // eslint-disable-next-line react/immutability
        posAttr.needsUpdate = true;
        const lineAttr = wireframeGeometry.getAttribute('position');
        for (let i = 0; i < wireIndices.length; i++) {
          const sourceIndex = wireIndices[i];
          if (sourceIndex >= 0) lineAttr.setXYZ(i, posAttr.getX(sourceIndex), posAttr.getY(sourceIndex), posAttr.getZ(sourceIndex));
        }
        // eslint-disable-next-line react/immutability -- Three.js animation buffer update.
        lineAttr.needsUpdate = true;
      }
    }

    // Aura pulse
    if (auraRef.current) {
      const auraScale = 1.0 + Math.sin(t * 1.5) * 0.05 + (state === 'SPEAKING' ? waveformLevel * 0.15 : 0);
      auraRef.current.scale.set(auraScale, auraScale, 1);
    }
  });

  return (
    <group position={[0, 0, 0]} scale={[1, 1, 1]}>
      {/* Background Holographic Radial Aura */}
      <mesh ref={auraRef} position={[0, 0, -0.6]}>
        <planeGeometry args={[3.8, 3.8]} />
        <meshBasicMaterial
          map={auraTexture}
          transparent
          opacity={0.85}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Semi-transparent Dark Facets catching depth */}
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          color="#001828"
          roughness={0.1}
          metalness={0.9}
          transparent
          opacity={0.35}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Primary Cyan Triangular Wireframe Lines */}
      <lineSegments ref={wireframeRef} geometry={wireframeGeometry}>
        <lineBasicMaterial
          color={state === 'ERROR' ? '#FF5533' : '#00FFFF'}
          transparent
          opacity={state === 'LISTENING' || state === 'SPEAKING' ? 0.95 : 0.7}
          blending={THREE.AdditiveBlending}
          linewidth={1.5}
        />
      </lineSegments>

      {/* Glowing Nodes / Vertices dots */}
      <points ref={nodesRef} geometry={geometry}>
        <pointsMaterial
          map={nodeTexture}
          color={state === 'ERROR' ? '#FFAA33' : '#B9F8FF'}
          size={0.065}
          transparent
          opacity={0.9}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>

      {/* Glowing Eye Pupils (Matching video circles) */}
      <group ref={pupilsRef}>
        {/* Right Pupil */}
        <mesh position={[0.36, 0.27, 0.74]}>
          <planeGeometry args={[0.22, 0.22]} />
          <meshBasicMaterial
            map={pupilTexture}
            transparent
            opacity={0.95}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>

        {/* Left Pupil */}
        <mesh position={[-0.36, 0.27, 0.74]}>
          <planeGeometry args={[0.22, 0.22]} />
          <meshBasicMaterial
            map={pupilTexture}
            transparent
            opacity={0.95}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
      </group>

      {/* Subtle Cyan Key Light */}
      <ambientLight intensity={0.5} />
      <pointLight position={[0, 0.5, 3]} color="#00FFFF" intensity={2.0} distance={8} />
      <pointLight position={[2, -1, 2]} color="#8057E9" intensity={1.0} distance={6} />
      <pointLight position={[-2, -1, 2]} color="#00E5E5" intensity={1.0} distance={6} />
    </group>
  );
};

export const HolographicFace: React.FC<HolographicFaceProps> = ({
  state,
  waveformLevel,
  lowPowerMode = false,
  minimal = false,
}) => {
  return (
    <div className={`w-full h-full relative select-none ${minimal ? 'bg-black' : 'bg-obsidian'}`}>
      <Canvas
        dpr={lowPowerMode ? 1 : [1, 1.75]}
        camera={{ position: [0, 0, 4.4], fov: 42 }}
        gl={{ antialias: !lowPowerMode, alpha: true, powerPreference: 'high-performance' }}
        onCreated={({ gl }) => {
          gl.setClearColor(minimal ? 0x000000 : 0x050b13, 1);
        }}
      >
        <ReferenceHolographicFace state={state} waveformLevel={waveformLevel} />
      </Canvas>

      {/* Subtle vignette */}
      <div className="absolute inset-0 pointer-events-none bg-radial-gradient from-transparent via-obsidian/40 to-obsidian" />
    </div>
  );
};
