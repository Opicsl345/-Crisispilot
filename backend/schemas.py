from pydantic import BaseModel, Field
from typing import Optional

class CitizenReportInput(BaseModel):
    reporter_name: Optional[str] = Field("Anonymous Citizen", description="Name of person submitting report")
    phone_number: Optional[str] = Field("N/A", description="Contact phone number")
    latitude: float = Field(..., description="GPS Latitude")
    longitude: float = Field(..., description="GPS Longitude")
    disaster_type: str = Field(..., description="Landslide, Flood, Fire, Blocked Road, Medical Emergency")
    people_affected: int = Field(0, ge=0, description="Total people in area")
    people_needing_rescue: int = Field(0, ge=0, description="People requiring urgent extraction")
    road_blocked: bool = Field(False, description="Is primary access road impassable?")
    description: str = Field(..., description="Detailed description of ground reality")