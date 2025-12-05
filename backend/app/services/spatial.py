from sqlalchemy.orm import Session
from sqlalchemy import text
import math
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

class VerisSpatialError(Exception):
    pass

class SpatialService:
    """
    World-class spatial operations for agricultural field management
    """
    
    @staticmethod
    async def calculate_field_metrics(boundary_coordinates: List[List[float]], 
                                    db: Session) -> Dict[str, Any]:
        """
        Calculate field area and center from GPS boundary coordinates
        
        Args:
            boundary_coordinates: List of [longitude, latitude] pairs
            db: Database session
            
        Returns:
            Dict with area_hectares, center_lat, center_lng, boundary_wkt
        """
        try:
            # Validate coordinates
            if len(boundary_coordinates) < 4:
                raise VerisSpatialError("Field boundary requires minimum 4 coordinate pairs")
            
            # Ensure polygon is closed
            if boundary_coordinates[0] != boundary_coordinates[-1]:
                boundary_coordinates.append(boundary_coordinates[0])
            
            # Create WKT polygon string
            coords_wkt = ",".join([f"{lng} {lat}" for lng, lat in boundary_coordinates])
            boundary_wkt = f"POLYGON(({coords_wkt}))"
            
            # Calculate area using PostGIS (accurate spherical calculation)
            # Casting to geometry/geography for area calculation
            area_query = text("""
                SELECT ST_Area(ST_Transform(ST_GeomFromText(:wkt, 4326), 3857)) / 10000.0 as area_hectares
            """)
            area_result = db.execute(area_query, {"wkt": boundary_wkt})
            area_hectares = area_result.scalar()
            
            # Calculate centroid
            centroid_query = text("""
                SELECT ST_Y(ST_Centroid(ST_GeomFromText(:wkt, 4326))) as lat,
                       ST_X(ST_Centroid(ST_GeomFromText(:wkt, 4326))) as lng
            """)
            centroid_result = db.execute(centroid_query, {"wkt": boundary_wkt})
            centroid_row = centroid_result.fetchone()
            
            return {
                "area_hectares": round(float(area_hectares), 4),
                "center_lat": float(centroid_row.lat),
                "center_lng": float(centroid_row.lng),
                "boundary_wkt": boundary_wkt
            }
            
        except Exception as e:
            raise VerisSpatialError(f"Failed to calculate field metrics: {str(e)}")
    
    @staticmethod
    async def generate_sampling_points(field_boundary_wkt: str, 
                                     min_samples: int,
                                     method: str = "random",
                                     edge_buffer_meters: float = 5.0,
                                     min_distance_meters: float = 20.0,
                                     db: Session = None) -> List[Dict[str, Any]]:
        """
        Generate GPS sampling points within field boundary using USDA methodology
        
        This is the core Verisca differentiator - automated, unbiased sampling
        """
        try:
            # Get field bounds from database for accurate calculations
            bounds_query = text("""
                SELECT ST_XMin(geom) as min_lng, ST_YMin(geom) as min_lat,
                       ST_XMax(geom) as max_lng, ST_YMax(geom) as max_lat
                FROM (SELECT ST_GeomFromText(:wkt, 4326) as geom) as subq
            """)
            bounds_result = db.execute(bounds_query, {"wkt": field_boundary_wkt})
            bounds = bounds_result.fetchone()
            
            # Convert buffer distances to degree approximations
            # At equator: 1 degree ≈ 111,000 meters
            # Adjusted for latitude (approximate for Zimbabwe: -17 to -22 degrees)
            lat_center = (bounds.min_lat + bounds.max_lat) / 2
            meters_per_degree = 111000 * abs(math.cos(math.radians(lat_center)))
            
            edge_buffer_degrees = edge_buffer_meters / meters_per_degree
            
            # Generate sample points
            points = []
            max_attempts = min_samples * 100  # Prevent infinite loops
            attempts = 0
            
            while len(points) < min_samples and attempts < max_attempts:
                # Generate random candidate point
                candidate_lng = random.uniform(bounds.min_lng, bounds.max_lng)
                candidate_lat = random.uniform(bounds.min_lat, bounds.max_lat)
                
                # Check if point is inside field with buffer
                # Note: ST_Buffer with negative value shrinks the polygon
                inside_check = text("""
                    SELECT ST_Contains(
                        ST_Buffer(ST_GeomFromText(:wkt, 4326), :buffer),
                        ST_Point(:lng, :lat)
                    )
                """)
                
                # buffer is in degrees, so we need to be careful. 
                # For basic POINT/POLYGON in 4326, ST_Buffer unit is degrees.
                # -edge_buffer_degrees effectively shrinks the polygon boundary.
                inside_result = db.execute(inside_check, {
                    "wkt": field_boundary_wkt,
                    "buffer": -edge_buffer_degrees, 
                    "lng": candidate_lng,
                    "lat": candidate_lat
                })
                
                if not inside_result.scalar():
                    attempts += 1
                    continue
                
                # Check minimum distance from other points
                too_close = False
                for point in points:
                    dist = SpatialService._calculate_distance(
                        candidate_lat, candidate_lng,
                        point['lat'], point['lng']
                    )
                    if dist < min_distance_meters:
                        too_close = True
                        break
                
                if too_close:
                    attempts += 1
                    continue
                
                # Calculate distance from field edge for quality assessment
                edge_distance_query = text("""
                    SELECT ST_Distance(
                        ST_Transform(ST_GeomFromText('POINT(' || :lng || ' ' || :lat || ')', 4326), 3857),
                        ST_Transform(ST_Boundary(ST_GeomFromText(:wkt, 4326)), 3857)
                    ) as distance_meters
                """)
                
                edge_result = db.execute(edge_distance_query, {
                    "lng": candidate_lng,
                    "lat": candidate_lat,
                    "wkt": field_boundary_wkt
                })
                
                edge_distance = edge_result.scalar()
                
                # Add point to collection
                points.append({
                    "sample_number": len(points) + 1,
                    "lat": round(candidate_lat, 7),  # ~1cm precision
                    "lng": round(candidate_lng, 7),
                    "distance_from_edge_meters": round(float(edge_distance), 1),
                    "gps_accuracy_required": "sub_meter",  # Mobile app guidance
                    "sampling_notes": f"Random point {len(points) + 1} of {min_samples}"
                })
                
                attempts += 1
            
            if len(points) < min_samples:
                # Fallback or warning if strict constraints prevent finding points
                # For now we raise validation error
                raise VerisSpatialError(
                    f"Could only generate {len(points)} of {min_samples} required points. "
                    f"Field may be too small or constraints too restrictive."
                )
            
            return points
            
        except Exception as e:
            if isinstance(e, VerisSpatialError):
                raise e
            raise VerisSpatialError(f"Sampling point generation failed: {str(e)}")
    
    @staticmethod
    def _calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS points using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Earth radius in meters
        
        return c * r
    
    @staticmethod
    async def validate_field_boundary(coordinates: List[List[float]], 
                                    db: Session) -> Dict[str, Any]:
        """
        Comprehensive field boundary validation
        """
        try:
            # Basic coordinate validation
            if len(coordinates) < 4:
                return {"valid": False, "error": "Minimum 4 coordinate pairs required"}
            
            # Ensure closed polygon
            coords = coordinates.copy()
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            
            # Check coordinate ranges (rough bounds for Africa/Zimbabwe context)
            for lng, lat in coords:
                if not (-180 <= lng <= 180):
                    return {"valid": False, "error": f"Invalid longitude: {lng}"}
                if not (-90 <= lat <= 90):
                    return {"valid": False, "error": f"Invalid latitude: {lat}"}
            
            # Create polygon and validate with PostGIS
            coords_wkt = ",".join([f"{lng} {lat}" for lng, lat in coords])
            boundary_wkt = f"POLYGON(({coords_wkt}))"
            
            # Check self-intersection and other geometry issues
            validation_query = text("""
                SELECT 
                    ST_IsValid(ST_GeomFromText(:wkt, 4326)) as is_valid,
                    ST_IsValidReason(ST_GeomFromText(:wkt, 4326)) as reason,
                    ST_Area(ST_Transform(ST_GeomFromText(:wkt, 4326), 3857)) / 10000.0 as area_hectares,
                    ST_NumPoints(ST_GeomFromText(:wkt, 4326)) as num_points
            """)
            
            result = db.execute(validation_query, {"wkt": boundary_wkt})
            row = result.fetchone()
            
            if not row.is_valid:
                return {"valid": False, "error": f"Invalid polygon geometry: {row.reason}"}
            
            if row.area_hectares < 0.01:  # Minimum 100 square meters
                return {"valid": False, "error": "Field too small (minimum 0.01 hectares)"}
                
            if row.area_hectares > 10000:  # Maximum 10,000 hectares
                return {"valid": False, "error": "Field too large (maximum 10,000 hectares)"}
            
            return {
                "valid": True,
                "area_hectares": round(float(row.area_hectares), 4),
                "num_points": int(row.num_points),
                "boundary_wkt": boundary_wkt
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
