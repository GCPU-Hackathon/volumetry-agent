import os
import glob
import json
from typing import Dict, List, Tuple
from pathlib import Path
import nibabel as nib
import numpy as np
import pandas as pd

class VolumetryService:
    def __init__(self):
        self.labels_dict = {1: "ET", 2: "WT", 3: "TC"}  # BraTS convention
    
    def hemispheric_volume(self, seg_data: np.ndarray, label: int, axis: int = 0) -> Tuple[int, int]:
        """
        Calculate hemispheric volume asymmetry.
        
        Args:
            seg_data: Segmentation data array
            label: Label value to analyze
            axis: Axis for hemisphere division (0 = sagittal)
            
        Returns:
            Tuple of (left_volume, right_volume)
        """
        mid = seg_data.shape[axis] // 2
        left = np.sum(seg_data[:mid] == label)
        right = np.sum(seg_data[mid:] == label)
        return left, right
    
    def process_study(self, study_code: str, filename: str) -> Dict:
        """
        Process a study and generate volumetry metrics.
        
        Args:
            study_code: Study identifier/directory name
            filename: Name of the segmentation file
            
        Returns:
            Dictionary with processing results
        """
        study_dir = Path("storage") / "studies" / study_code
        
        if not study_dir.exists():
            raise FileNotFoundError(f"Study directory not found: {study_dir}")
        
        # Use the provided filename
        seg_file = study_dir / filename
        
        if not seg_file.exists():
            raise FileNotFoundError(f"Segmentation file not found: {seg_file}")
        
        results = []
        
        patient = filename.split(".")[0]  # Use filename without extension as patient ID
        
        try:
            # Load segmentation file
            seg_nii = nib.load(str(seg_file))
            seg_data = seg_nii.get_fdata()
            voxel_volume_ml = np.prod(seg_nii.header.get_zooms()) / 1000  # mm³ → mL
            affine = seg_nii.affine
            
            # Process each label
            for label, name in self.labels_dict.items():
                count = np.sum(seg_data == label)
                volume_mL = count * voxel_volume_ml
                
                # Calculate hemispheric asymmetry
                left, right = self.hemispheric_volume(seg_data, label)
                asymmetry_index = (left - right) / (left + right) if (left + right) > 0 else 0
                
                # Calculate centroid in mm coordinates
                coords = np.argwhere(seg_data == label)
                if len(coords) > 0:
                    centroid_voxel = np.mean(coords, axis=0)
                    centroid_mm = nib.affines.apply_affine(affine, centroid_voxel)
                else:
                    centroid_mm = (np.nan, np.nan, np.nan)
                
                results.append({
                    "patient": patient,
                    "label": name,
                    "volume_mL": float(volume_mL),
                    "asymmetry_index": float(asymmetry_index),
                    "centroid_x_mm": float(centroid_mm[0]),
                    "centroid_y_mm": float(centroid_mm[1]),
                    "centroid_z_mm": float(centroid_mm[2])
                })
            
        except Exception as e:
            raise Exception(f"Error processing file {seg_file}: {str(e)}")
        
        # Save metrics as JSON
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
        """
        Retrieve existing metrics for a study.
        
        Args:
            study_code: Study identifier
            
        Returns:
            Dictionary containing the metrics
        """
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
