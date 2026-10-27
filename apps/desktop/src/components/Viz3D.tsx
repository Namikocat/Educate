/** Three.js solids of revolution / cross-sections. Loaded lazily (dynamic import) to keep startup fast. */
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Fn1 } from "@viz/expr";
import { getBackend } from "../lib/backend";

export interface Solid {
  f: Fn1;
  g?: Fn1;
  a: number;
  b: number;
  axis: "x" | "y";
  axisValue?: number;
  method: "disk" | "washer" | "shell" | "surface" | "cross_section";
  shape?: "square" | "semicircle" | "equilateral";
  sweep: number;   // radians 0..2π
  slices: number;  // number of disks / shells shown
}

function material(color: number, opacity = 0.85) {
  return new THREE.MeshStandardMaterial({ color, side: THREE.DoubleSide, transparent: opacity < 1, opacity, metalness: 0.05, roughness: 0.6 });
}

function build(s: Solid): THREE.Group {
  const grp = new THREE.Group();
  const N = 80, seg = 64;
  const c = s.axisValue ?? 0;
  if (s.method === "cross_section") {
    // base along x, cross-sections perpendicular to x with side = f(x)
    const dx = (s.b - s.a) / s.slices;
    for (let i = 0; i < s.slices; i++) {
      const x = s.a + (i + 0.5) * dx, side = Math.max(0, s.f(x));
      let geo: THREE.BufferGeometry;
      if (s.shape === "semicircle") geo = new THREE.CylinderGeometry(side / 2, side / 2, dx * 0.9, 24, 1, false, 0, Math.PI);
      else if (s.shape === "equilateral") {
        const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(side, 0); sh.lineTo(side / 2, (Math.sqrt(3) / 2) * side); sh.closePath();
        geo = new THREE.ExtrudeGeometry(sh, { depth: dx * 0.9, bevelEnabled: false });
      } else geo = new THREE.BoxGeometry(dx * 0.9, side, side);
      const m = new THREE.Mesh(geo, material(0x3b82f6, 0.8));
      if (s.shape === "semicircle") { m.rotation.z = Math.PI / 2; m.rotation.y = Math.PI / 2; m.position.set(x, 0, side / 2); }
      else if (s.shape === "equilateral") { m.rotation.y = Math.PI / 2; m.position.set(x - dx * 0.45, 0, side); m.rotation.x = Math.PI / 2; }
      else m.position.set(x, side / 2, side / 2);
      grp.add(m);
    }
    return grp;
  }
  // profile radius r(t) measured from the rotation axis, t along the axis
  const radius = (fn: Fn1, t: number) => Math.abs(fn(t) - c);
  const lathe = (fn: Fn1, color: number, opacity: number) => {
    const pts: THREE.Vector2[] = [];
    for (let i = 0; i <= N; i++) {
      const t = s.a + ((s.b - s.a) * i) / N, r = radius(fn, t);
      if (Number.isFinite(r)) pts.push(new THREE.Vector2(r, t));
    }
    const geo = new THREE.LatheGeometry(pts, seg, 0, s.sweep);
    return new THREE.Mesh(geo, material(color, opacity));
  };
  if (s.method === "shell") {
    // cylinders around the axis x = c (axis "y" in the plane) with height f(x) (or f-g)
    const dx = (s.b - s.a) / s.slices;
    for (let i = 0; i < s.slices; i++) {
      const x = s.a + (i + 0.5) * dx, r = Math.abs(x - c);
      const top = s.f(x), bot = s.g ? s.g(x) : 0, h = Math.abs(top - bot);
      if (!Number.isFinite(h) || h < 1e-6) continue;
      const geo = new THREE.CylinderGeometry(r, r, h, seg, 1, true, 0, s.sweep);
      const m = new THREE.Mesh(geo, material(i % 2 ? 0x60a5fa : 0x2563eb, 0.55));
      m.position.y = (top + bot) / 2;
      grp.add(m);
    }
    grp.position.x = c; // shells are built around the local y-axis
    const wrap = new THREE.Group(); wrap.add(grp); return wrap;
  }
  const outer = lathe(s.f, 0x3b82f6, s.method === "surface" ? 0.9 : 0.75);
  grp.add(outer);
  if (s.method === "washer" && s.g) grp.add(lathe(s.g, 0xef4444, 0.9));
  if (s.method === "disk" || s.method === "washer") {
    const dx = (s.b - s.a) / s.slices;
    for (let i = 0; i <= s.slices; i++) {
      const t = s.a + i * dx, R = radius(s.f, t), r = s.g ? radius(s.g, t) : 0;
      const ring = new THREE.Mesh(new THREE.RingGeometry(Math.min(r, R), Math.max(r, R), seg, 1, 0, s.sweep), material(0x1d4ed8, 0.35));
      ring.rotation.x = -Math.PI / 2; ring.position.y = t; grp.add(ring);
    }
  }
  // LatheGeometry revolves around local Y: map Y to the requested axis
  if (s.axis === "x") { grp.rotation.z = -Math.PI / 2; grp.position.y = c; }
  return grp;
}

export default function Viz3D({ solid }: { solid: Solid }) {
  const host = useRef<HTMLDivElement>(null);
  const state = useRef<{ renderer: THREE.WebGLRenderer; scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: OrbitControls; obj?: THREE.Object3D; raf: number } | null>(null);

  useEffect(() => {
    const el = host.current!;
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(el.clientWidth, 380);
    renderer.setClearColor(0xffffff);
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, el.clientWidth / 380, 0.01, 500);
    camera.position.set(6, 5, 8);
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(5, 10, 7); scene.add(dl);
    scene.add(new THREE.AxesHelper(4));
    const grid = new THREE.GridHelper(10, 10, 0xd1d5db, 0xe5e7eb); grid.rotation.x = Math.PI / 2; scene.add(grid);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    const tick = () => { controls.update(); renderer.render(scene, camera); st.raf = requestAnimationFrame(tick); };
    const st = { renderer, scene, camera, controls, raf: 0 } as NonNullable<typeof state.current>;
    state.current = st;
    tick();
    const onResize = () => { renderer.setSize(el.clientWidth, 380); camera.aspect = el.clientWidth / 380; camera.updateProjectionMatrix(); };
    window.addEventListener("resize", onResize);
    return () => { cancelAnimationFrame(st.raf); window.removeEventListener("resize", onResize); controls.dispose(); renderer.dispose(); el.removeChild(renderer.domElement); };
  }, []);

  useEffect(() => {
    const st = state.current; if (!st) return;
    if (st.obj) { st.scene.remove(st.obj); st.obj.traverse((o) => { if (o instanceof THREE.Mesh) { o.geometry.dispose(); (o.material as THREE.Material).dispose(); } }); }
    const obj = build(solid);
    st.scene.add(obj); st.obj = obj;
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3()).length() || 4, center = box.getCenter(new THREE.Vector3());
    st.controls.target.copy(center);
    st.camera.position.copy(center.clone().add(new THREE.Vector3(size * 0.9, size * 0.6, size * 1.1)));
  }, [solid]);

  const [saved, setSaved] = useState<string | null>(null);
  const exportPng = () => {
    const url = state.current?.renderer.domElement.toDataURL("image/png");
    if (!url) return;
    getBackend().then((be) => be.saveFile(`solid-${Date.now()}.png`, url, true)).then(setSaved, (e) => setSaved(String(e)));
  };
  return (
    <div>
      <div ref={host} className="w-full overflow-hidden rounded-lg border border-line" aria-label="ภาพสามมิติ หมุนด้วยการลากเมาส์" role="img" />
      <div className="mt-1 flex gap-2 text-xs"><button className="rounded border border-line px-2 py-0.5" onClick={exportPng}>บันทึกภาพ PNG</button>
        <span className="text-muted">ลากเพื่อหมุน · ล้อเมาส์เพื่อซูม · คลิกขวาลากเพื่อเลื่อน</span>{saved && <span className="text-good">บันทึกแล้ว: {saved}</span>}</div>
    </div>
  );
}
