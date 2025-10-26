import os
import glob
import json
from typing import Dict, List, Tuple
from pathlib import Path
import nibabel as nib
import numpy as np
import pandas as pd
from nibabel.orientations import aff2axcodes

class VolumetryService:
    def __init__(self):
        # Ton mapping actuel (déjà remappé en amont)
        self.labels_dict = {1: "ET", 2: "WT", 3: "TC"}
        
    def _centroid_mm(self, affine: np.ndarray, coords_vox: np.ndarray) -> Tuple[float,float,float]:
        if coords_vox.size == 0:
            return (float('nan'), float('nan'), float('nan'))
        centroid_voxel = np.mean(coords_vox, axis=0)
        cx, cy, cz = nib.affines.apply_affine(affine, centroid_voxel)
        return float(cx), float(cy), float(cz)

    def _hemispheric_counts(self, affine: np.ndarray, coords_vox: np.ndarray, mid_x_mm: float) -> Tuple[int,int]:
        """Compte gauche/droite en monde (mm) par rapport à un plan médian x = mid_x_mm."""
        if coords_vox.size == 0:
            return 0, 0
        xyz = nib.affines.apply_affine(affine, coords_vox)  # (N,3)
        left = int(np.sum(xyz[:, 0] <  mid_x_mm))
        right = int(np.sum(xyz[:, 0] >= mid_x_mm))
        return left, right

    def process_study(self, study_code: str, filename: str) -> Dict:
        study_dir = Path("storage") / "studies" / study_code
        if not study_dir.exists():
            raise FileNotFoundError(f"Study directory not found: {study_dir}")

        seg_file = study_dir / filename
        if not seg_file.exists():
            raise FileNotFoundError(f"Segmentation file not found: {seg_file}")

        results = []
        patient = filename.split(".")[0]

        try:
            # 1) Chargement + RAS canonique (IMPORTANT)
            seg_nii = nib.load(str(seg_file))
            seg_nii = nib.as_closest_canonical(seg_nii)
            seg_data = seg_nii.get_fdata()
            affine = seg_nii.affine
            voxel_volume_ml = np.prod(seg_nii.header.get_zooms()) / 1000.0  # mm^3 -> mL

            # Log orientation au cas où
            axcodes = aff2axcodes(affine)  # attendu ('R','A','S')
            # print(f"Orientation (attendu RAS): {axcodes}")

            # 2) Plan médian robuste: médiane des x monde de toute la segmentation (seg>0)
            brain_idx = np.argwhere(seg_data > 0)
            if brain_idx.size > 0:
                brain_xyz = nib.affines.apply_affine(affine, brain_idx)
                mid_x_mm = np.median(brain_xyz[:, 0])
            else:
                # fallback si la segmentation est vide
                # on prend le milieu géométrique en monde
                shape = np.array(seg_data.shape, dtype=float)
                mid_vox = (shape - 1) / 2.0
                mid_x_mm = float(nib.affines.apply_affine(affine, mid_vox)[0])

            # 3) Calculs par label
            # --- Mode actuel "déjà remappé": 1=ET, 2=WT, 3=TC ---
            for label, name in self.labels_dict.items():
                mask = (seg_data == label)
                coords = np.argwhere(mask)

                count_vox = int(coords.shape[0])
                volume_mL = float(count_vox * voxel_volume_ml)

                left, right = self._hemispheric_counts(affine, coords, mid_x_mm)
                asymmetry_index = float((left - right) / (left + right)) if (left + right) > 0 else 0.0

                cx, cy, cz = self._centroid_mm(affine, coords)

                results.append({
                    "patient": patient,
                    "label": name,
                    "volume_mL": volume_mL,
                    "asymmetry_index": asymmetry_index,
                    "centroid_x_mm": cx,
                    "centroid_y_mm": cy,
                    "centroid_z_mm": cz
                })

        except Exception as e:
            raise Exception(f"Error processing file {seg_file}: {str(e)}")

        # 4) Sauvegarde
        metrics_file = study_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(results, f, indent=2)

        return {
            "processed_files": 1,
            "metrics_count": len(results),
            "metrics_saved": True,
            "metrics_file": str(metrics_file)
        }

    def get_study_metrics(self, study_code: str) -> Dict:
        study_dir = Path("storage") / "studies" / study_code
        metrics_file = study_dir / "metrics.json"
        if not metrics_file.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        return {
            "study_code": study_code,
            "metrics": metrics,
            "total_records": len(metrics)
        }
