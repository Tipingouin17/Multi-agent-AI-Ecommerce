"""
Warehouse Capacity & Workforce Management Service - Multi-Agent E-commerce System

This service handles warehouse capacity planning and workforce management including:
- Workforce capacity tracking (headcount, shifts, skills)
- Throughput metrics (orders per hour, units per hour)
- Space utilization and capacity planning
- Equipment and resource management
- Performance analytics and KPIs
- Peak capacity vs current utilization
- Bottleneck identification
"""

from typing import Dict, List, Optional
from datetime import datetime, time, timedelta
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import structlog
from shared.base_agent_v2 import BaseAgentV2
from typing import Any

logger = structlog.get_logger(__name__)


# ===========================
# ENUMS
# ===========================

class EmployeeRole(str, Enum):
    """Employee role in warehouse."""
    PICKER = "picker"
    PACKER = "packer"
    RECEIVER = "receiver"
    SHIPPER = "shipper"
    FORKLIFT_OPERATOR = "forklift_operator"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    QUALITY_CONTROL = "quality_control"


class ShiftType(str, Enum):
    """Shift type."""
    MORNING = "morning"  # 6am-2pm
    AFTERNOON = "afternoon"  # 2pm-10pm
    NIGHT = "night"  # 10pm-6am
    FULL_DAY = "full_day"  # 8am-5pm


class SkillLevel(str, Enum):
    """Employee skill level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EquipmentType(str, Enum):
    """Type of warehouse equipment."""
    FORKLIFT = "forklift"
    PALLET_JACK = "pallet_jack"
    SCANNER = "scanner"
    CONVEYOR = "conveyor"
    SORTING_MACHINE = "sorting_machine"
    PACKAGING_MACHINE = "packaging_machine"


# ===========================
# PYDANTIC MODELS
# ===========================

class Employee(BaseModel):
    """Warehouse employee."""
    employee_id: str
    name: str
    role: EmployeeRole
    skill_level: SkillLevel
    hourly_rate: Decimal
    shift: ShiftType
    is_active: bool = True
    hire_date: datetime
    certifications: List[str] = []
    
    # Performance metrics
    avg_picks_per_hour: Optional[Decimal] = None
    avg_packs_per_hour: Optional[Decimal] = None
    accuracy_rate: Optional[Decimal] = None


class Shift(BaseModel):
    """Warehouse shift definition."""
    shift_id: str
    shift_type: ShiftType
    start_time: time
    end_time: time
    capacity: int  # Max employees
    current_headcount: int = 0
    required_roles: Dict[EmployeeRole, int] = {}


class WarehouseCapacity(BaseModel):
    """Warehouse capacity metrics."""
    warehouse_id: str
    date: datetime
    
    # Space metrics
    total_space_sqft: Decimal
    used_space_sqft: Decimal
    available_space_sqft: Decimal
    utilization_rate: Decimal  # Percentage
    
    # Workforce metrics
    total_employees: int
    active_employees: int
    employees_by_role: Dict[str, int]
    
    # Throughput metrics
    orders_per_hour_capacity: Decimal
    current_orders_per_hour: Decimal
    units_per_hour_capacity: Decimal
    current_units_per_hour: Decimal
    
    # Equipment metrics
    total_equipment: int
    available_equipment: int
    equipment_utilization: Decimal


class ThroughputMetrics(BaseModel):
    """Warehouse throughput metrics."""
    warehouse_id: str
    period_start: datetime
    period_end: datetime
    
    # Order metrics
    total_orders_processed: int
    orders_per_hour: Decimal
    orders_per_employee: Decimal
    
    # Unit metrics
    total_units_processed: int
    units_per_hour: Decimal
    units_per_employee: Decimal
    
    # Time metrics
    avg_order_cycle_time: Decimal  # Minutes
    avg_pick_time: Decimal  # Minutes
    avg_pack_time: Decimal  # Minutes
    
    # Quality metrics
    accuracy_rate: Decimal  # Percentage
    error_rate: Decimal  # Percentage


class CapacityForecast(BaseModel):
    """Capacity forecast for planning."""
    warehouse_id: str
    forecast_date: datetime
    
    # Demand forecast
    expected_orders: int
    expected_units: int
    
    # Capacity requirements
    required_employees: int
    required_equipment: int
    required_space_sqft: Decimal
    
    # Gap analysis
    employee_gap: int  # Negative if shortage
    equipment_gap: int
    space_gap: Decimal
    
    # Recommendations
    recommendations: List[str] = []


class Equipment(BaseModel):
    """Warehouse equipment."""
    equipment_id: str
    equipment_type: EquipmentType
    name: str
    is_available: bool = True
    is_operational: bool = True
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    assigned_to: Optional[str] = None  # Employee ID
    utilization_rate: Optional[Decimal] = None


class PerformanceKPIs(BaseModel):
    """Warehouse performance KPIs."""
    warehouse_id: str
    period_start: datetime
    period_end: datetime
    
    # Efficiency KPIs
    order_fill_rate: Decimal  # Percentage
    on_time_delivery_rate: Decimal
    order_accuracy: Decimal
    inventory_accuracy: Decimal
    
    # Productivity KPIs
    picks_per_labor_hour: Decimal
    lines_per_labor_hour: Decimal
    orders_per_labor_hour: Decimal
    
    # Cost KPIs
    cost_per_order: Decimal
    labor_cost_percentage: Decimal
    overtime_percentage: Decimal
    
    # Space KPIs
    storage_utilization: Decimal
    dock_utilization: Decimal
    
    # Safety KPIs
    incident_rate: Decimal
    near_miss_count: int


# ===========================
# WAREHOUSE CAPACITY SERVICE
# ===========================

class WarehouseCapacityService(BaseAgentV2):
    """Service for warehouse capacity and workforce management."""
    
    def __init__(self, agent_id: str = "warehousecapacityservice_001", db_manager=None):
        super().__init__(agent_id=agent_id)
        self.db_manager = db_manager
        self.logger = logger.bind(service="warehouse_capacity")
    
    async def get_current_capacity(self, warehouse_id: str) -> WarehouseCapacity:
        """Get current warehouse capacity metrics."""
        async with self.db_manager.get_async_session() as session:
            # Get space metrics
            space_query = """
                SELECT 
                    total_space_sqft,
                    used_space_sqft,
                    (total_space_sqft - used_space_sqft) as available_space_sqft,
                    (used_space_sqft / total_space_sqft * 100) as utilization_rate
                FROM warehouse_capacity
                WHERE warehouse_id = $1
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            space_result = await session.execute(space_query, warehouse_id)
            space_row = space_result.fetchone()
            
            if not space_row:
                raise ValueError(f"Warehouse {warehouse_id} not found")
            
            # Get workforce metrics
            workforce_query = """
                SELECT 
                    COUNT(*) as total_employees,
                    COUNT(*) FILTER (WHERE is_active = true) as active_employees,
                    role,
                    COUNT(*) as count
                FROM warehouse_employees
                WHERE warehouse_id = $1
                GROUP BY role
            """
            
            workforce_result = await session.execute(workforce_query, warehouse_id)
            workforce_rows = workforce_result.fetchall()
            
            employees_by_role = {row[2]: row[3] for row in workforce_rows}
            total_employees = sum(employees_by_role.values())
            
            # Get throughput metrics
            throughput_query = """
                SELECT 
                    orders_per_hour_capacity,
                    current_orders_per_hour,
                    units_per_hour_capacity,
                    current_units_per_hour
                FROM warehouse_throughput
                WHERE warehouse_id = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            throughput_result = await session.execute(throughput_query, warehouse_id)
            throughput_row = throughput_result.fetchone()
            
            # Get equipment metrics
            equipment_query = """
                SELECT 
                    COUNT(*) as total_equipment,
                    COUNT(*) FILTER (WHERE is_available = true AND is_operational = true) as available_equipment
                FROM warehouse_equipment
                WHERE warehouse_id = $1
            """
            
            equipment_result = await session.execute(equipment_query, warehouse_id)
            equipment_row = equipment_result.fetchone()
            
            equipment_utilization = Decimal('0')
            if equipment_row[0] > 0:
                equipment_utilization = Decimal(str(equipment_row[1])) / Decimal(str(equipment_row[0])) * Decimal('100')
            
            return WarehouseCapacity(
                warehouse_id=warehouse_id,
                date=datetime.utcnow(),
                total_space_sqft=Decimal(str(space_row[0])),
                used_space_sqft=Decimal(str(space_row[1])),
                available_space_sqft=Decimal(str(space_row[2])),
                utilization_rate=Decimal(str(space_row[3])),
                total_employees=total_employees,
                active_employees=total_employees,  # Simplified
                employees_by_role=employees_by_role,
                orders_per_hour_capacity=Decimal(str(throughput_row[0])) if throughput_row else Decimal('0'),
                current_orders_per_hour=Decimal(str(throughput_row[1])) if throughput_row else Decimal('0'),
                units_per_hour_capacity=Decimal(str(throughput_row[2])) if throughput_row else Decimal('0'),
                current_units_per_hour=Decimal(str(throughput_row[3])) if throughput_row else Decimal('0'),
                total_equipment=equipment_row[0] if equipment_row else 0,
                available_equipment=equipment_row[1] if equipment_row else 0,
                equipment_utilization=equipment_utilization
            )
    
    async def calculate_throughput_metrics(
        self,
        warehouse_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> ThroughputMetrics:
        """Calculate throughput metrics for a period."""
        async with self.db_manager.get_async_session() as session:
            # Calculate order metrics
            order_query = """
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(DISTINCT employee_id) as total_employees,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_cycle_time,
                    AVG(EXTRACT(EPOCH FROM (picked_at - started_at))/60) as avg_pick_time,
                    AVG(EXTRACT(EPOCH FROM (packed_at - picked_at))/60) as avg_pack_time,
                    COUNT(*) FILTER (WHERE is_accurate = true)::DECIMAL / COUNT(*) * 100 as accuracy_rate
                FROM warehouse_order_processing
                WHERE warehouse_id = $1
                  AND completed_at BETWEEN $2 AND $3
            """
            
            order_result = await session.execute(order_query, warehouse_id, period_start, period_end)
            order_row = order_result.fetchone()
            
            # Calculate unit metrics
            unit_query = """
                SELECT 
                    SUM(quantity) as total_units
                FROM warehouse_order_items
                WHERE warehouse_id = $1
                  AND processed_at BETWEEN $2 AND $3
            """
            
            unit_result = await session.execute(unit_query, warehouse_id, period_start, period_end)
            unit_row = unit_result.fetchone()
            
            # Calculate time period in hours
            period_hours = (period_end - period_start).total_seconds() / 3600
            
            total_orders = order_row[0] if order_row else 0
            total_employees = order_row[1] if order_row else 1
            total_units = unit_row[0] if unit_row and unit_row[0] else 0
            
            orders_per_hour = Decimal(str(total_orders)) / Decimal(str(period_hours)) if period_hours > 0 else Decimal('0')
            units_per_hour = Decimal(str(total_units)) / Decimal(str(period_hours)) if period_hours > 0 else Decimal('0')
            
            return ThroughputMetrics(
                warehouse_id=warehouse_id,
                period_start=period_start,
                period_end=period_end,
                total_orders_processed=total_orders,
                orders_per_hour=orders_per_hour,
                orders_per_employee=Decimal(str(total_orders)) / Decimal(str(total_employees)),
                total_units_processed=total_units,
                units_per_hour=units_per_hour,
                units_per_employee=Decimal(str(total_units)) / Decimal(str(total_employees)),
                avg_order_cycle_time=Decimal(str(order_row[2])) if order_row and order_row[2] else Decimal('0'),
                avg_pick_time=Decimal(str(order_row[3])) if order_row and order_row[3] else Decimal('0'),
                avg_pack_time=Decimal(str(order_row[4])) if order_row and order_row[4] else Decimal('0'),
                accuracy_rate=Decimal(str(order_row[5])) if order_row and order_row[5] else Decimal('0'),
                error_rate=Decimal('100') - (Decimal(str(order_row[5])) if order_row and order_row[5] else Decimal('0'))
            )
    
    async def forecast_capacity_needs(
        self,
        warehouse_id: str,
        forecast_date: datetime,
        expected_orders: int,
        expected_units: int
    ) -> CapacityForecast:
        """Forecast capacity needs based on expected demand."""
        # Get current capacity
        current_capacity = await self.get_current_capacity(warehouse_id)
        
        # Calculate required resources
        # Assume 10 orders per employee per hour, 8-hour shift
        required_employees = int((expected_orders / 10 / 8) + 0.5)  # Round up
        
        # Assume 1 piece of equipment per 5 employees
        required_equipment = int((required_employees / 5) + 0.5)
        
        # Assume 100 sqft per 1000 units
        required_space = Decimal(str(expected_units)) / Decimal('1000') * Decimal('100')
        
        # Calculate gaps
        employee_gap = required_employees - current_capacity.active_employees
        equipment_gap = required_equipment - current_capacity.available_equipment
        space_gap = required_space - current_capacity.available_space_sqft
        
        # Generate recommendations
        recommendations = []
        if employee_gap > 0:
            recommendations.append(f"Hire {employee_gap} additional employees")
        if equipment_gap > 0:
            recommendations.append(f"Acquire {equipment_gap} additional equipment units")
        if space_gap > 0:
            recommendations.append(f"Expand warehouse by {float(space_gap):.0f} sqft")
        
        if not recommendations:
            recommendations.append("Current capacity is sufficient")
        
        return CapacityForecast(
            warehouse_id=warehouse_id,
            forecast_date=forecast_date,
            expected_orders=expected_orders,
            expected_units=expected_units,
            required_employees=required_employees,
            required_equipment=required_equipment,
            required_space_sqft=required_space,
            employee_gap=employee_gap,
            equipment_gap=equipment_gap,
            space_gap=space_gap,
            recommendations=recommendations
        )
    
    async def get_performance_kpis(
        self,
        warehouse_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> PerformanceKPIs:
        """Calculate warehouse performance KPIs."""
        async with self.db_manager.get_async_session() as session:
            # Get efficiency metrics
            efficiency_query = """
                SELECT 
                    COUNT(*) FILTER (WHERE is_fulfilled = true)::DECIMAL / COUNT(*) * 100 as fill_rate,
                    COUNT(*) FILTER (WHERE delivered_on_time = true)::DECIMAL / COUNT(*) * 100 as on_time_rate,
                    COUNT(*) FILTER (WHERE is_accurate = true)::DECIMAL / COUNT(*) * 100 as accuracy_rate
                FROM warehouse_orders
                WHERE warehouse_id = $1
                  AND completed_at BETWEEN $2 AND $3
            """
            
            efficiency_result = await session.execute(efficiency_query, warehouse_id, period_start, period_end)
            efficiency_row = efficiency_result.fetchone()
            
            # Get productivity metrics
            throughput = await self.calculate_throughput_metrics(warehouse_id, period_start, period_end)
            
            # Get cost metrics
            cost_query = """
                SELECT 
                    AVG(total_cost) as avg_cost_per_order,
                    SUM(labor_cost) / SUM(total_cost) * 100 as labor_cost_pct,
                    SUM(overtime_hours) / SUM(total_hours) * 100 as overtime_pct
                FROM warehouse_costs
                WHERE warehouse_id = $1
                  AND date BETWEEN $2 AND $3
            """
            
            cost_result = await session.execute(cost_query, warehouse_id, period_start, period_end)
            cost_row = cost_result.fetchone()
            
            # Get space metrics
            capacity = await self.get_current_capacity(warehouse_id)
            
            # Get safety metrics
            safety_query = """
                SELECT 
                    COUNT(*) as incident_count,
                    COUNT(*) FILTER (WHERE is_near_miss = true) as near_miss_count,
                    SUM(total_hours_worked) as total_hours
                FROM warehouse_safety_incidents
                WHERE warehouse_id = $1
                  AND incident_date BETWEEN $2 AND $3
            """
            
            safety_result = await session.execute(safety_query, warehouse_id, period_start, period_end)
            safety_row = safety_result.fetchone()
            
            incident_rate = Decimal('0')
            if safety_row and safety_row[2]:
                # OSHA incident rate = (incidents / total hours) * 200,000
                incident_rate = Decimal(str(safety_row[0])) / Decimal(str(safety_row[2])) * Decimal('200000')
            
            return PerformanceKPIs(
                warehouse_id=warehouse_id,
                period_start=period_start,
                period_end=period_end,
                order_fill_rate=Decimal(str(efficiency_row[0])) if efficiency_row and efficiency_row[0] else Decimal('0'),
                on_time_delivery_rate=Decimal(str(efficiency_row[1])) if efficiency_row and efficiency_row[1] else Decimal('0'),
                order_accuracy=Decimal(str(efficiency_row[2])) if efficiency_row and efficiency_row[2] else Decimal('0'),
                inventory_accuracy=Decimal('95.0'),  # Placeholder
                picks_per_labor_hour=throughput.units_per_hour,
                lines_per_labor_hour=throughput.orders_per_hour,
                orders_per_labor_hour=throughput.orders_per_hour,
                cost_per_order=Decimal(str(cost_row[0])) if cost_row and cost_row[0] else Decimal('0'),
                labor_cost_percentage=Decimal(str(cost_row[1])) if cost_row and cost_row[1] else Decimal('0'),
                overtime_percentage=Decimal(str(cost_row[2])) if cost_row and cost_row[2] else Decimal('0'),
                storage_utilization=capacity.utilization_rate,
                dock_utilization=Decimal('75.0'),  # Placeholder
                incident_rate=incident_rate,
                near_miss_count=safety_row[1] if safety_row else 0
            )
    
    async def add_employee(self, warehouse_id: str, employee: Employee):
        """Add a new employee to the warehouse."""
        async with self.db_manager.get_async_session() as session:
            try:
                insert_query = """
                    INSERT INTO warehouse_employees (
                        warehouse_id, employee_id, name, role, skill_level,
                        hourly_rate, shift, is_active, hire_date, certifications
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                
                await session.execute(
                    insert_query,
                    warehouse_id,
                    employee.employee_id,
                    employee.name,
                    employee.role.value,
                    employee.skill_level.value,
                    float(employee.hourly_rate),
                    employee.shift.value,
                    employee.is_active,
                    employee.hire_date,
                    employee.certifications
                )
                
                await session.commit()
                
                self.logger.info("Added employee",
                               warehouse_id=warehouse_id,
                               employee_id=employee.employee_id,
                               role=employee.role.value)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to add employee",
                                error=str(e),
                                warehouse_id=warehouse_id)
                raise
    
    async def add_equipment(self, warehouse_id: str, equipment: Equipment):
        """Add new equipment to the warehouse."""
        async with self.db_manager.get_async_session() as session:
            try:
                insert_query = """
                    INSERT INTO warehouse_equipment (
                        warehouse_id, equipment_id, equipment_type, name,
                        is_available, is_operational, last_maintenance, next_maintenance
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                await session.execute(
                    insert_query,
                    warehouse_id,
                    equipment.equipment_id,
                    equipment.equipment_type.value,
                    equipment.name,
                    equipment.is_available,
                    equipment.is_operational,
                    equipment.last_maintenance,
                    equipment.next_maintenance
                )
                
                await session.commit()
                
                self.logger.info("Added equipment",
                               warehouse_id=warehouse_id,
                               equipment_id=equipment.equipment_id,
                               equipment_type=equipment.equipment_type.value)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to add equipment",
                                error=str(e),
                                warehouse_id=warehouse_id)
                raise
    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        logger.info(f"{self.__class__.__name__} initialized successfully")
    
    async def cleanup(self):
        """Cleanup service resources."""
        try:
            await super().cleanup()
            logger.info(f"{self.__class__.__name__} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing {self.__class__.__name__} operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}

