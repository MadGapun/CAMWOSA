import {
  useRohmaterialStore,
  type NullpunktReferenz,
  type RohmaterialForm,
} from "../state/rohmaterialStore";

export default function RohmaterialEditor() {
  const r = useRohmaterialStore((s) => s.rohmaterial);
  const setze = useRohmaterialStore((s) => s.setze);

  return (
    <div className="grid grid-cols-4 gap-2 text-xs">
      <label>
        <span className="text-camwosa-muted">Form</span>
        <select
          className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.form}
          onChange={(e) => setze({ form: e.target.value as RohmaterialForm })}
        >
          <option value="platte">Platte</option>
          <option value="quader">Quader</option>
          <option value="zylinder">Zylinder</option>
          <option value="frei">Frei (DXF-/STL-Bound)</option>
        </select>
      </label>
      <label>
        <span className="text-camwosa-muted">
          {r.form === "zylinder" ? "Durchmesser" : "Laenge"} (mm)
        </span>
        <input
          type="number" className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.laenge} step={1}
          onChange={(e) => setze({ laenge: parseFloat(e.target.value) || 0 })}
        />
      </label>
      <label>
        <span className="text-camwosa-muted">
          {r.form === "zylinder" ? "Laenge" : "Breite"} (mm)
        </span>
        <input
          type="number" className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.breite} step={1}
          onChange={(e) => setze({ breite: parseFloat(e.target.value) || 0 })}
        />
      </label>
      <label>
        <span className="text-camwosa-muted">Hoehe (mm)</span>
        <input
          type="number" className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.hoehe} step={0.5}
          onChange={(e) => setze({ hoehe: parseFloat(e.target.value) || 0 })}
        />
      </label>
      <label>
        <span className="text-camwosa-muted">Nullpunkt X (mm)</span>
        <input
          type="number" className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.nullpunkt[0]} step={0.5}
          onChange={(e) => setze({
            nullpunkt: [parseFloat(e.target.value) || 0, r.nullpunkt[1], r.nullpunkt[2]],
          })}
        />
      </label>
      <label>
        <span className="text-camwosa-muted">Nullpunkt Y (mm)</span>
        <input
          type="number" className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.nullpunkt[1]} step={0.5}
          onChange={(e) => setze({
            nullpunkt: [r.nullpunkt[0], parseFloat(e.target.value) || 0, r.nullpunkt[2]],
          })}
        />
      </label>
      <label>
        <span className="text-camwosa-muted">Nullpunkt Z (mm)</span>
        <input
          type="number" className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.nullpunkt[2]} step={0.5}
          onChange={(e) => setze({
            nullpunkt: [r.nullpunkt[0], r.nullpunkt[1], parseFloat(e.target.value) || 0],
          })}
        />
      </label>
      <label>
        <span className="text-camwosa-muted">Z-Referenz</span>
        <select
          className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1"
          value={r.z_referenz}
          onChange={(e) => setze({ z_referenz: e.target.value as NullpunktReferenz })}
        >
          <option value="material_top">Material Top</option>
          <option value="material_bottom">Material Bottom</option>
          <option value="tisch_top">Tisch Top</option>
        </select>
      </label>
    </div>
  );
}
