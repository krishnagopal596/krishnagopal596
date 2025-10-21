#!/usr/bin/env python3
"""
Intelligent Motion Analyzer
Advanced computer vision system for real-time human motion analysis

Author: Krishna Gopal Madhavaram
Email: krishnagopal596@gmail.com
"""

import cv2
import numpy as np
import mediapipe as mp
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    GAIT_ANALYSIS = "gait_analysis"
    POSE_ESTIMATION = "pose_estimation"
    BIOMECHANICAL = "biomechanical"
    INJURY_RISK = "injury_risk"

@dataclass
class PoseLandmark:
    """Represents a single pose landmark with 3D coordinates and visibility"""
    x: float
    y: float
    z: float
    visibility: float

@dataclass
class JointAngle:
    """Represents joint angle measurement"""
    joint_name: str
    angle_degrees: float
    confidence: float

@dataclass
class MotionMetrics:
    """Container for motion analysis results"""
    frame_id: int
    timestamp: float
    poses: List[Dict]
    joint_angles: List[JointAngle]
    gait_metrics: Optional[Dict] = None
    biomechanical_data: Optional[Dict] = None

class PoseEstimator:
    """Advanced pose estimation using MediaPipe with custom enhancements"""
    
    def __init__(self, model_complexity: int = 2, min_detection_confidence: float = 0.7):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5
        )
        
        # Landmark indices for key joints
        self.joint_connections = {
            'left_leg': [23, 25, 27, 29, 31],  # Hip to foot
            'right_leg': [24, 26, 28, 30, 32],
            'left_arm': [11, 13, 15, 17, 19, 21],  # Shoulder to hand
            'right_arm': [12, 14, 16, 18, 20, 22],
            'spine': [11, 12, 23, 24]  # Shoulders and hips
        }
    
    def detect_pose(self, frame: np.ndarray) -> Optional[List[PoseLandmark]]:
        """
        Detect human pose in the given frame
        
        Args:
            frame: Input image frame (BGR format)
            
        Returns:
            List of pose landmarks or None if no pose detected
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append(PoseLandmark(
                        x=landmark.x,
                        y=landmark.y,
                        z=landmark.z,
                        visibility=landmark.visibility
                    ))
                return landmarks
            
            return None
            
        except Exception as e:
            logger.error(f"Error in pose detection: {e}")
            return None
    
    def calculate_joint_angles(self, landmarks: List[PoseLandmark]) -> List[JointAngle]:
        """
        Calculate joint angles from pose landmarks
        
        Args:
            landmarks: List of pose landmarks
            
        Returns:
            List of joint angles
        """
        joint_angles = []
        
        try:
            # Calculate knee angles
            left_knee_angle = self._calculate_angle(
                landmarks[23], landmarks[25], landmarks[27]  # Hip, Knee, Ankle
            )
            right_knee_angle = self._calculate_angle(
                landmarks[24], landmarks[26], landmarks[28]
            )
            
            # Calculate hip angles
            left_hip_angle = self._calculate_angle(
                landmarks[11], landmarks[23], landmarks[25]  # Shoulder, Hip, Knee
            )
            right_hip_angle = self._calculate_angle(
                landmarks[12], landmarks[24], landmarks[26]
            )
            
            # Calculate ankle angles
            left_ankle_angle = self._calculate_angle(
                landmarks[25], landmarks[27], landmarks[29]  # Knee, Ankle, Foot
            )
            right_ankle_angle = self._calculate_angle(
                landmarks[26], landmarks[28], landmarks[30]
            )
            
            joint_angles.extend([
                JointAngle("left_knee", left_knee_angle, landmarks[25].visibility),
                JointAngle("right_knee", right_knee_angle, landmarks[26].visibility),
                JointAngle("left_hip", left_hip_angle, landmarks[23].visibility),
                JointAngle("right_hip", right_hip_angle, landmarks[24].visibility),
                JointAngle("left_ankle", left_ankle_angle, landmarks[27].visibility),
                JointAngle("right_ankle", right_ankle_angle, landmarks[28].visibility)
            ])
            
        except Exception as e:
            logger.error(f"Error calculating joint angles: {e}")
        
        return joint_angles
    
    def _calculate_angle(self, point1: PoseLandmark, point2: PoseLandmark, point3: PoseLandmark) -> float:
        """Calculate angle between three points"""
        try:
            # Convert to numpy arrays for easier calculation
            p1 = np.array([point1.x, point1.y])
            p2 = np.array([point2.x, point2.y])
            p3 = np.array([point3.x, point3.y])
            
            # Calculate vectors
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Calculate angle
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Avoid numerical errors
            
            angle = np.arccos(cos_angle)
            return np.degrees(angle)
            
        except Exception as e:
            logger.error(f"Error calculating angle: {e}")
            return 0.0

class GaitAnalyzer:
    """Advanced gait analysis for movement pattern assessment"""
    
    def __init__(self):
        self.step_history = []
        self.stride_history = []
        self.cadence_history = []
    
    def analyze_gait(self, landmarks: List[PoseLandmark], frame_id: int) -> Dict:
        """
        Analyze gait pattern from pose landmarks
        
        Args:
            landmarks: Current frame pose landmarks
            frame_id: Frame identifier
            
        Returns:
            Dictionary containing gait analysis results
        """
        try:
            # Extract foot positions
            left_foot = landmarks[31] if len(landmarks) > 31 else None
            right_foot = landmarks[32] if len(landmarks) > 32 else None
            
            if not left_foot or not right_foot:
                return {"error": "Insufficient landmark data"}
            
            # Calculate step length
            step_length = self._calculate_step_length(left_foot, right_foot)
            
            # Calculate cadence (steps per minute)
            cadence = self._calculate_cadence(frame_id)
            
            # Calculate symmetry
            symmetry_score = self._calculate_symmetry(landmarks)
            
            # Detect gait phases
            gait_phase = self._detect_gait_phase(landmarks)
            
            return {
                "step_length": step_length,
                "cadence": cadence,
                "symmetry_score": symmetry_score,
                "gait_phase": gait_phase,
                "frame_id": frame_id,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in gait analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_step_length(self, left_foot: PoseLandmark, right_foot: PoseLandmark) -> float:
        """Calculate step length between feet"""
        try:
            distance = np.sqrt(
                (left_foot.x - right_foot.x)**2 + 
                (left_foot.y - right_foot.y)**2
            )
            return distance
        except:
            return 0.0
    
    def _calculate_cadence(self, frame_id: int) -> float:
        """Calculate cadence (steps per minute)"""
        # Simplified implementation - would need more sophisticated tracking
        return 120.0  # Placeholder
    
    def _calculate_symmetry(self, landmarks: List[PoseLandmark]) -> float:
        """Calculate gait symmetry score"""
        try:
            # Compare left and right leg joint angles
            left_knee = landmarks[25]
            right_knee = landmarks[26]
            
            # Calculate symmetry based on joint positions
            symmetry = 1.0 - abs(left_knee.y - right_knee.y)
            return max(0.0, min(1.0, symmetry))
        except:
            return 0.5
    
    def _detect_gait_phase(self, landmarks: List[PoseLandmark]) -> str:
        """Detect current gait phase (stance, swing, etc.)"""
        # Simplified implementation
        return "stance"  # Placeholder

class BiomechanicalAnalyzer:
    """Biomechanical analysis for injury risk assessment"""
    
    def __init__(self):
        self.risk_factors = []
        self.movement_patterns = []
    
    def assess_injury_risk(self, motion_data: List[MotionMetrics]) -> Dict:
        """
        Assess injury risk based on movement patterns
        
        Args:
            motion_data: List of motion metrics over time
            
        Returns:
            Dictionary containing injury risk assessment
        """
        try:
            # Analyze movement patterns
            risk_factors = self._identify_risk_factors(motion_data)
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risk_factors)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_factors)
            
            return {
                "overall_risk_score": risk_score,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in injury risk assessment: {e}")
            return {"error": str(e)}
    
    def _identify_risk_factors(self, motion_data: List[MotionMetrics]) -> List[str]:
        """Identify potential injury risk factors"""
        risk_factors = []
        
        try:
            for metrics in motion_data:
                # Check for excessive knee valgus
                for angle in metrics.joint_angles:
                    if angle.joint_name == "left_knee" and angle.angle_degrees < 160:
                        risk_factors.append("excessive_knee_valgus_left")
                    elif angle.joint_name == "right_knee" and angle.angle_degrees < 160:
                        risk_factors.append("excessive_knee_valgus_right")
                
                # Check for asymmetry
                if metrics.gait_metrics and metrics.gait_metrics.get("symmetry_score", 1.0) < 0.8:
                    risk_factors.append("gait_asymmetry")
            
            return list(set(risk_factors))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return []
    
    def _calculate_risk_score(self, risk_factors: List[str]) -> float:
        """Calculate overall injury risk score (0-1)"""
        if not risk_factors:
            return 0.0
        
        # Simple scoring based on number of risk factors
        base_score = len(risk_factors) * 0.2
        return min(1.0, base_score)
    
    def _generate_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []
        
        if "excessive_knee_valgus" in str(risk_factors):
            recommendations.append("Focus on hip strengthening exercises")
            recommendations.append("Practice proper landing mechanics")
        
        if "gait_asymmetry" in risk_factors:
            recommendations.append("Work on balance and proprioception")
            recommendations.append("Consider physical therapy assessment")
        
        return recommendations

class MotionAnalyzer:
    """Main motion analysis orchestrator"""
    
    def __init__(self, analysis_type: AnalysisType = AnalysisType.GAIT_ANALYSIS):
        self.analysis_type = analysis_type
        self.pose_estimator = PoseEstimator()
        self.gait_analyzer = GaitAnalyzer()
        self.biomechanical_analyzer = BiomechanicalAnalyzer()
        self.motion_history = []
    
    def analyze_frame(self, frame: np.ndarray, frame_id: int) -> MotionMetrics:
        """
        Analyze a single frame for motion metrics
        
        Args:
            frame: Input image frame
            frame_id: Frame identifier
            
        Returns:
            MotionMetrics object with analysis results
        """
        try:
            # Detect pose
            landmarks = self.pose_estimator.detect_pose(frame)
            
            if landmarks is None:
                return MotionMetrics(
                    frame_id=frame_id,
                    timestamp=time.time(),
                    poses=[],
                    joint_angles=[]
                )
            
            # Calculate joint angles
            joint_angles = self.pose_estimator.calculate_joint_angles(landmarks)
            
            # Perform gait analysis
            gait_metrics = None
            if self.analysis_type == AnalysisType.GAIT_ANALYSIS:
                gait_metrics = self.gait_analyzer.analyze_gait(landmarks, frame_id)
            
            # Create motion metrics
            motion_metrics = MotionMetrics(
                frame_id=frame_id,
                timestamp=time.time(),
                poses=[{
                    "landmarks": [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility} 
                               for lm in landmarks]
                }],
                joint_angles=joint_angles,
                gait_metrics=gait_metrics
            )
            
            # Store in history
            self.motion_history.append(motion_metrics)
            
            return motion_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing frame {frame_id}: {e}")
            return MotionMetrics(
                frame_id=frame_id,
                timestamp=time.time(),
                poses=[],
                joint_angles=[]
            )
    
    def get_comprehensive_analysis(self) -> Dict:
        """Get comprehensive analysis of all motion data"""
        try:
            if not self.motion_history:
                return {"error": "No motion data available"}
            
            # Perform biomechanical analysis
            biomechanical_data = self.biomechanical_analyzer.assess_injury_risk(self.motion_history)
            
            return {
                "total_frames": len(self.motion_history),
                "analysis_duration": self.motion_history[-1].timestamp - self.motion_history[0].timestamp,
                "biomechanical_assessment": biomechanical_data,
                "motion_summary": self._generate_motion_summary()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {"error": str(e)}
    
    def _generate_motion_summary(self) -> Dict:
        """Generate summary of motion analysis"""
        try:
            if not self.motion_history:
                return {}
            
            # Calculate average joint angles
            avg_angles = {}
            for joint_name in ["left_knee", "right_knee", "left_hip", "right_hip"]:
                angles = [metrics.joint_angles for metrics in self.motion_history 
                         if metrics.joint_angles]
                if angles:
                    joint_angles = [angle.angle_degrees for angle_list in angles 
                                  for angle in angle_list if angle.joint_name == joint_name]
                    if joint_angles:
                        avg_angles[joint_name] = np.mean(joint_angles)
            
            return {
                "average_joint_angles": avg_angles,
                "total_poses_detected": len([m for m in self.motion_history if m.poses]),
                "analysis_type": self.analysis_type.value
            }
            
        except Exception as e:
            logger.error(f"Error generating motion summary: {e}")
            return {}

def main():
    """Main function for testing the motion analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent Motion Analyzer")
    parser.add_argument("--input", "-i", help="Input video file or camera index", default=0)
    parser.add_argument("--output", "-o", help="Output file for results", default="motion_analysis.json")
    parser.add_argument("--analysis-type", "-t", choices=[e.value for e in AnalysisType], 
                       default=AnalysisType.GAIT_ANALYSIS.value, help="Type of analysis to perform")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = MotionAnalyzer(AnalysisType(args.analysis_type))
    
    # Open video source
    if args.input.isdigit():
        cap = cv2.VideoCapture(int(args.input))
    else:
        cap = cv2.VideoCapture(args.input)
    
    if not cap.isOpened():
        logger.error("Error opening video source")
        return
    
    frame_id = 0
    results = []
    
    logger.info("Starting motion analysis...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze frame
            motion_metrics = analyzer.analyze_frame(frame, frame_id)
            results.append(motion_metrics)
            
            # Display frame with pose overlay
            if motion_metrics.poses:
                # Draw pose landmarks (simplified)
                for pose in motion_metrics.poses:
                    for landmark in pose["landmarks"]:
                        x = int(landmark["x"] * frame.shape[1])
                        y = int(landmark["y"] * frame.shape[0])
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            
            # Show frame
            cv2.imshow("Motion Analysis", frame)
            
            # Break on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            frame_id += 1
            
            # Limit analysis for demo
            if frame_id > 100:
                break
    
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Get comprehensive analysis
        comprehensive_analysis = analyzer.get_comprehensive_analysis()
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump({
                "frame_results": [
                    {
                        "frame_id": m.frame_id,
                        "timestamp": m.timestamp,
                        "poses": m.poses,
                        "joint_angles": [{"joint": ja.joint_name, "angle": ja.angle_degrees, 
                                        "confidence": ja.confidence} for ja in m.joint_angles],
                        "gait_metrics": m.gait_metrics
                    } for m in results
                ],
                "comprehensive_analysis": comprehensive_analysis
            }, f, indent=2)
        
        logger.info(f"Analysis complete. Results saved to {args.output}")

if __name__ == "__main__":
    main()
