from sqlalchemy import Column, Integer, Float, String, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class HistoricalListing(Base):
    __tablename__ = "historical_listings"
    

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(String) 
    price = Column(Float)
    type = Column(String)
    beds = Column(Integer)
    baths = Column(Integer)
    address = Column(String)
    furnishing = Column(String)
    completion_status = Column(String)
    post_date = Column(Date)
    building_name = Column(String)
    year_of_completion = Column(Integer)
    total_parking_spaces = Column(Integer)
    total_floors = Column(Integer)
    total_building_area_sqft = Column(Float)
    elevators = Column(Integer)
    area_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    link = Column(String)
    
    def __repr__(self):
        return f"<HistoricalListing(id='{self.id}', area='{self.area_name}')>"


class ActiveListing(Base):
    __tablename__ = "active_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(String, nullable=False)
    price = Column(Float)
    type = Column(String)
    beds = Column(Integer)
    baths = Column(Integer)
    address = Column(String)
    furnishing = Column(String)
    completion_status = Column(String)
    post_date = Column(Date)
    building_name = Column(String)
    year_of_completion = Column(Integer)
    total_parking_spaces = Column(Integer)
    total_floors = Column(Integer)
    total_building_area_sqft = Column(Float)
    elevators = Column(Integer)
    area_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    link = Column(String)

    __table_args__ = (
        UniqueConstraint("property_id", name="uix_active_property_id"),
    )

    def __repr__(self):
        return f"<ActiveListing(property_id='{self.property_id}', area='{self.area_name}')>"