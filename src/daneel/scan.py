"""Scan intake — make a photogrammetry mesh printable (``daneel import``).

Photogrammetry meshes are typically non-manifold, high-poly, arbitrarily scaled and
oriented. :func:`prepare` repairs, scales, seats the mesh on the bed and optionally
decimates it, then reports what it did so the result can be sanity-checked before slicing.
Needs the optional ``[scan]`` extra (trimesh, numpy, scipy, fast-simplification).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class ScanError(RuntimeError):
    pass


@dataclass
class ImportReport:
    faces_in: int
    faces_out: int
    watertight: bool
    scale: float
    extents_mm: tuple[float, float, float]
    notes: list[str] = field(default_factory=list)


def scale_from_reference(real_mm: float, model_units: float) -> float:
    """Scale factor that makes a reference feature (e.g. the calib cube edge) true size."""
    if real_mm <= 0 or model_units <= 0:
        raise ScanError("reference sizes must be positive")
    return real_mm / model_units


def _trimesh():  # noqa: ANN202 - optional dependency
    try:
        import trimesh
    except ImportError as exc:
        raise ScanError('trimesh missing: pip install -e ".[scan]"') from exc
    return trimesh


def prepare(
    src: str | Path,
    dst: str | Path,
    *,
    scale: float = 1.0,
    max_faces: int | None = None,
    auto_orient: bool = False,
) -> ImportReport:
    """Repair, scale, orient and (optionally) decimate ``src``; write STL to ``dst``."""
    trimesh = _trimesh()
    if scale <= 0:
        raise ScanError("scale must be positive")
    try:
        loaded = trimesh.load(str(src), force="mesh", process=False)
    except Exception as exc:
        raise ScanError(f"cannot read {src}: {exc}") from exc
    if not isinstance(loaded, trimesh.Trimesh) or len(loaded.faces) == 0:
        raise ScanError(f"{src} contains no mesh faces")

    mesh = loaded
    faces_in = len(mesh.faces)
    notes: list[str] = []

    # Photogrammetry output has duplicate vertices and degenerate triangles.
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()

    # Keep the largest connected component: scans carry floating debris.
    parts = mesh.split(only_watertight=False)
    if len(parts) > 1:
        mesh = max(parts, key=lambda m: len(m.faces))
        notes.append(f"dropped {len(parts) - 1} disconnected fragment(s)")

    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fill_holes(mesh)

    if max_faces is not None and len(mesh.faces) > max_faces:
        try:
            mesh = mesh.simplify_quadric_decimation(face_count=max_faces)
        except Exception as exc:
            raise ScanError(
                f"decimation failed (is fast-simplification installed?): {exc}"
            ) from exc
        notes.append(f"decimated to {len(mesh.faces)} faces")

    if scale != 1.0:
        mesh.apply_scale(scale)

    if auto_orient:
        try:
            poses, _ = mesh.compute_stable_poses(n_samples=1)
            mesh.apply_transform(poses[0])
            notes.append("auto-oriented onto most stable face")
        except Exception as exc:
            notes.append(f"auto-orient skipped: {exc}")

    # Seat on the bed (z=0) and centre in XY.
    lo, hi = mesh.bounds
    mesh.apply_translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))

    if not mesh.is_watertight:
        notes.append("mesh is not watertight; the slicer may need to repair it")

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(dst))
    ex = mesh.extents
    return ImportReport(
        faces_in=faces_in,
        faces_out=len(mesh.faces),
        watertight=bool(mesh.is_watertight),
        scale=scale,
        extents_mm=(float(ex[0]), float(ex[1]), float(ex[2])),
        notes=notes,
    )
