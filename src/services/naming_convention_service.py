"""Service for managing VM naming conventions and analysis."""

import logging
import re
from datetime import datetime

from sqlalchemy.orm import Session

from src.models import Label, NamingConvention, NamingConventionField, VirtualMachine, VMLabel, VMNamingAnalysis

logger = logging.getLogger(__name__)


class NamingConventionError(Exception):
    """Base exception for naming convention errors."""

    pass


class PatternValidationError(NamingConventionError):
    """Exception raised when pattern validation fails."""

    pass


class NamingConventionService:
    """Service for managing VM naming conventions and analysis."""

    def __init__(self, session: Session):
        """Initialize the service with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def create_convention(
        self,
        name: str,
        pattern: str,
        fields: list[dict],
        description: str | None = None,
        created_by: str | None = None,
    ) -> NamingConvention:
        """Create a new naming convention.

        Args:
            name: Unique name for the convention
            pattern: Pattern string (e.g., "<D><Y><K><S><XXX><YYY>")
            fields: List of field definitions with position, length, name, etc.
            description: Optional description
            created_by: Username of creator

        Returns:
            Created NamingConvention instance

        Raises:
            PatternValidationError: If pattern or fields are invalid
            NamingConventionError: If convention with name already exists
        """
        logger.info(f"Creating naming convention: {name}")

        # Check if convention already exists
        existing = self.session.query(NamingConvention).filter_by(name=name).first()
        if existing:
            raise NamingConventionError(f"Convention with name '{name}' already exists")

        # Validate pattern and fields
        self._validate_pattern_and_fields(pattern, fields)

        # Calculate total length
        total_length = sum(field["length"] for field in fields)

        # Create convention
        convention = NamingConvention(
            name=name,
            pattern=pattern,
            description=description,
            total_length=total_length,
            is_active=True,
            created_by=created_by,
        )
        self.session.add(convention)
        self.session.flush()  # Get ID without committing

        # Create fields
        for field_data in fields:
            field = NamingConventionField(
                convention_id=convention.id,
                field_name=field_data["field_name"],
                position=field_data["position"],
                length=field_data["length"],
                description=field_data.get("description"),
                possible_values=field_data.get("possible_values"),
                is_required=field_data.get("is_required", True),
                validation_regex=field_data.get("validation_regex"),
            )
            self.session.add(field)

        self.session.commit()
        self.session.refresh(convention)

        logger.info(f"Created naming convention '{name}' with ID {convention.id}")
        return convention

    def update_convention(
        self,
        convention_id: int,
        name: str | None = None,
        pattern: str | None = None,
        fields: list[dict] | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> NamingConvention:
        """Update an existing naming convention.

        Args:
            convention_id: ID of convention to update
            name: New name (optional)
            pattern: New pattern (optional)
            fields: New field definitions (optional, replaces all fields)
            description: New description (optional)
            is_active: Active status (optional)

        Returns:
            Updated NamingConvention instance

        Raises:
            NamingConventionError: If convention not found or validation fails
        """
        logger.info(f"Updating naming convention ID: {convention_id}")

        convention = self.session.query(NamingConvention).get(convention_id)
        if not convention:
            raise NamingConventionError(f"Convention with ID {convention_id} not found")

        # Update fields
        if name is not None:
            # Check for name conflict
            existing = (
                self.session.query(NamingConvention)
                .filter(NamingConvention.name == name, NamingConvention.id != convention_id)
                .first()
            )
            if existing:
                raise NamingConventionError(f"Convention with name '{name}' already exists")
            convention.name = name

        if pattern is not None:
            convention.pattern = pattern

        if description is not None:
            convention.description = description

        if is_active is not None:
            convention.is_active = is_active

        # If fields are provided, replace all existing fields
        if fields is not None:
            # Validate new fields with pattern
            self._validate_pattern_and_fields(pattern or convention.pattern, fields)

            # Delete existing fields
            self.session.query(NamingConventionField).filter_by(convention_id=convention_id).delete()

            # Create new fields
            for field_data in fields:
                field = NamingConventionField(
                    convention_id=convention_id,
                    field_name=field_data["field_name"],
                    position=field_data["position"],
                    length=field_data["length"],
                    description=field_data.get("description"),
                    possible_values=field_data.get("possible_values"),
                    is_required=field_data.get("is_required", True),
                    validation_regex=field_data.get("validation_regex"),
                )
                self.session.add(field)

            # Update total length
            convention.total_length = sum(field["length"] for field in fields)

        convention.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(convention)

        logger.info(f"Updated naming convention ID {convention_id}")
        return convention

    def delete_convention(self, convention_id: int) -> None:
        """Delete a naming convention and all associated data.

        Args:
            convention_id: ID of convention to delete

        Raises:
            NamingConventionError: If convention not found
        """
        logger.info(f"Deleting naming convention ID: {convention_id}")

        convention = self.session.query(NamingConvention).get(convention_id)
        if not convention:
            raise NamingConventionError(f"Convention with ID {convention_id} not found")

        self.session.delete(convention)
        self.session.commit()

        logger.info(f"Deleted naming convention ID {convention_id}")

    def get_convention(self, convention_id: int) -> NamingConvention | None:
        """Get a naming convention by ID.

        Args:
            convention_id: ID of convention

        Returns:
            NamingConvention instance or None if not found
        """
        return self.session.query(NamingConvention).get(convention_id)

    def list_conventions(self, active_only: bool = False, include_fields: bool = True) -> list[NamingConvention]:
        """List all naming conventions.

        Args:
            active_only: If True, only return active conventions
            include_fields: If True, eagerly load fields

        Returns:
            List of NamingConvention instances
        """
        query = self.session.query(NamingConvention)

        if active_only:
            query = query.filter_by(is_active=True)

        conventions = query.order_by(NamingConvention.name).all()

        # Fields are loaded automatically via relationship if accessed
        return conventions

    def parse_vm_name(self, vm_name: str, convention: NamingConvention) -> tuple[bool, dict[str, str], list[str]]:
        """Parse a VM name according to a naming convention.

        Args:
            vm_name: VM name to parse
            convention: NamingConvention to use for parsing

        Returns:
            Tuple of (is_valid, field_values, errors)
            - is_valid: True if name matches convention
            - field_values: Dictionary mapping field names to extracted values
            - errors: List of validation error messages
        """
        field_values = {}
        errors = []

        # Check total length
        if convention.total_length and len(vm_name) != convention.total_length:
            errors.append(f"VM name length {len(vm_name)} does not match expected length " f"{convention.total_length}")
            return False, field_values, errors

        # Sort fields by position
        fields = sorted(convention.fields, key=lambda f: f.position)

        # Extract values for each field
        current_pos = 0
        for field in fields:
            if current_pos + field.length > len(vm_name):
                errors.append(
                    f"VM name too short to extract field '{field.field_name}' " f"at position {field.position}"
                )
                field_values[field.field_name] = None
                continue

            # Extract value
            value = vm_name[current_pos : current_pos + field.length]
            field_values[field.field_name] = value

            # Validate against possible values if defined
            if field.possible_values and isinstance(field.possible_values, list):
                if value not in field.possible_values:
                    errors.append(
                        f"Field '{field.field_name}' value '{value}' not in allowed values: " f"{field.possible_values}"
                    )

            # Validate against regex if defined
            if field.validation_regex:
                try:
                    if not re.match(field.validation_regex, value):
                        errors.append(
                            f"Field '{field.field_name}' value '{value}' does not match "
                            f"pattern '{field.validation_regex}'"
                        )
                except re.error as e:
                    logger.error(f"Invalid regex for field '{field.field_name}': {e}")
                    errors.append(f"Invalid validation regex for field '{field.field_name}'")

            # Check if required field is empty
            if field.is_required and not value.strip():
                errors.append(f"Required field '{field.field_name}' is empty")

            current_pos += field.length

        is_valid = len(errors) == 0
        return is_valid, field_values, errors

    def analyze_vm_inventory(
        self, convention_id: int, vm_filter: dict | None = None, batch_size: int = 100
    ) -> dict[str, int]:
        """Analyze VM inventory against a naming convention.

        Args:
            convention_id: ID of convention to use
            vm_filter: Optional filters for VMs (e.g., {'datacenter': 'DC1'})
            batch_size: Number of VMs to process per batch

        Returns:
            Dictionary with statistics:
            - total: Total VMs analyzed
            - valid: Number of valid matches
            - invalid: Number of invalid matches
            - updated: Number of analysis records updated
            - created: Number of new analysis records

        Raises:
            NamingConventionError: If convention not found
        """
        logger.info(f"Analyzing VM inventory with convention ID {convention_id}")

        convention = self.get_convention(convention_id)
        if not convention:
            raise NamingConventionError(f"Convention with ID {convention_id} not found")

        # Build VM query
        query = self.session.query(VirtualMachine)

        if vm_filter:
            for key, value in vm_filter.items():
                if hasattr(VirtualMachine, key):
                    query = query.filter(getattr(VirtualMachine, key) == value)

        total_vms = query.count()
        logger.info(f"Found {total_vms} VMs to analyze")

        stats = {"total": total_vms, "valid": 0, "invalid": 0, "updated": 0, "created": 0}

        # Process VMs in batches
        offset = 0
        while offset < total_vms:
            vms = query.limit(batch_size).offset(offset).all()

            for vm in vms:
                # Parse VM name
                is_valid, field_values, errors = self.parse_vm_name(vm.vm, convention)

                if is_valid:
                    stats["valid"] += 1
                else:
                    stats["invalid"] += 1

                # Check if analysis record exists
                existing = (
                    self.session.query(VMNamingAnalysis).filter_by(vm_id=vm.id, convention_id=convention_id).first()
                )

                if existing:
                    # Update existing record
                    existing.vm_name = vm.vm
                    existing.field_values = field_values
                    existing.is_valid = is_valid
                    existing.validation_errors = {"errors": errors} if errors else None
                    existing.analyzed_at = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Create new record
                    analysis = VMNamingAnalysis(
                        vm_id=vm.id,
                        convention_id=convention_id,
                        vm_name=vm.vm,
                        field_values=field_values,
                        is_valid=is_valid,
                        validation_errors={"errors": errors} if errors else None,
                    )
                    self.session.add(analysis)
                    stats["created"] += 1

            self.session.commit()
            offset += batch_size
            logger.debug(f"Processed {offset}/{total_vms} VMs")

        logger.info(f"Analysis complete: {stats}")
        return stats

    def analyze_vm_inventory_multi(
        self,
        convention_ids: list[int],
        vm_filter: dict | None = None,
        batch_size: int = 100,
        stop_on_first_match: bool = True,
    ) -> dict[str, any]:
        """Analyze VM inventory against multiple naming conventions.

        Args:
            convention_ids: List of convention IDs to use for analysis
            vm_filter: Optional filters for VMs (e.g., {'datacenter': 'DC1'})
            batch_size: Number of VMs to process per batch
            stop_on_first_match: If True, stop testing conventions after first valid match

        Returns:
            Dictionary with statistics:
            - total: Total VMs analyzed
            - matched: Number of VMs with at least one valid match
            - unmatched: Number of VMs with no valid matches
            - by_convention: Dict mapping convention_id to match count
            - multiple_matches: Number of VMs matching multiple conventions
            - records_created: Total analysis records created
            - records_updated: Total analysis records updated

        Raises:
            NamingConventionError: If any convention not found
        """
        logger.info(f"Analyzing VM inventory with {len(convention_ids)} conventions: {convention_ids}")

        # Validate all conventions exist
        conventions = []
        for conv_id in convention_ids:
            convention = self.get_convention(conv_id)
            if not convention:
                raise NamingConventionError(f"Convention with ID {conv_id} not found")
            conventions.append(convention)

        # Build VM query
        query = self.session.query(VirtualMachine)

        if vm_filter:
            for key, value in vm_filter.items():
                if hasattr(VirtualMachine, key):
                    query = query.filter(getattr(VirtualMachine, key) == value)

        total_vms = query.count()
        logger.info(f"Found {total_vms} VMs to analyze against {len(conventions)} conventions")

        stats = {
            "total": total_vms,
            "matched": 0,
            "unmatched": 0,
            "by_convention": dict.fromkeys(convention_ids, 0),
            "multiple_matches": 0,
            "records_created": 0,
            "records_updated": 0,
        }

        # Process VMs in batches
        offset = 0
        while offset < total_vms:
            vms = query.limit(batch_size).offset(offset).all()

            for vm in vms:
                vm_matched = False
                match_count = 0

                # Try each convention
                for convention in conventions:
                    # Parse VM name against this convention
                    is_valid, field_values, errors = self.parse_vm_name(vm.vm, convention)

                    if is_valid:
                        vm_matched = True
                        match_count += 1
                        stats["by_convention"][convention.id] += 1

                    # Check if analysis record exists
                    existing = (
                        self.session.query(VMNamingAnalysis).filter_by(vm_id=vm.id, convention_id=convention.id).first()
                    )

                    if existing:
                        # Update existing record
                        existing.vm_name = vm.vm
                        existing.field_values = field_values
                        existing.is_valid = is_valid
                        existing.validation_errors = {"errors": errors} if errors else None
                        existing.analyzed_at = datetime.utcnow()
                        stats["records_updated"] += 1
                    else:
                        # Create new record
                        analysis = VMNamingAnalysis(
                            vm_id=vm.id,
                            convention_id=convention.id,
                            vm_name=vm.vm,
                            field_values=field_values,
                            is_valid=is_valid,
                            validation_errors={"errors": errors} if errors else None,
                        )
                        self.session.add(analysis)
                        stats["records_created"] += 1

                    # Stop on first match if requested
                    if stop_on_first_match and is_valid:
                        break

                # Update match statistics
                if vm_matched:
                    stats["matched"] += 1
                    if match_count > 1:
                        stats["multiple_matches"] += 1
                else:
                    stats["unmatched"] += 1

            self.session.commit()
            offset += batch_size
            logger.debug(f"Processed {offset}/{total_vms} VMs")

        logger.info(f"Multi-convention analysis complete: {stats}")
        return stats

    def query_vms_by_field(
        self, convention_id: int, field_filters: dict[str, str], valid_only: bool = True
    ) -> list[VMNamingAnalysis]:
        """Query VMs by naming convention field values.

        Args:
            convention_id: ID of naming convention
            field_filters: Dictionary of field names to values (e.g., {'datacenter': 'D', 'env': 'P'})
            valid_only: If True, only return valid analyses

        Returns:
            List of VMNamingAnalysis records matching the filters
        """
        query = self.session.query(VMNamingAnalysis).filter_by(convention_id=convention_id)

        if valid_only:
            query = query.filter_by(is_valid=True)

        # Filter by field values using JSON queries
        # This is database-specific; adjust for your database
        for field_name, field_value in field_filters.items():
            # SQLite/PostgreSQL JSON query
            query = query.filter(VMNamingAnalysis.field_values[field_name].astext == field_value)

        return query.all()

    def generate_migration_groups(self, convention_id: int, grouping_fields: list[str]) -> list[dict]:
        """Generate migration groups based on naming convention fields.

        Args:
            convention_id: ID of naming convention
            grouping_fields: List of field names to group by

        Returns:
            List of dictionaries with group info:
            - group_key: Dictionary of field values defining the group
            - vm_count: Number of VMs in the group
            - vm_ids: List of VM IDs in the group

        Raises:
            NamingConventionError: If convention not found
        """
        logger.info(f"Generating migration groups for convention {convention_id}")

        convention = self.get_convention(convention_id)
        if not convention:
            raise NamingConventionError(f"Convention with ID {convention_id} not found")

        # Get all valid analyses
        analyses = self.session.query(VMNamingAnalysis).filter_by(convention_id=convention_id, is_valid=True).all()

        # Group by field values
        groups = {}
        for analysis in analyses:
            # Build group key from specified fields
            group_key = tuple(analysis.field_values.get(field, None) for field in grouping_fields)

            if group_key not in groups:
                groups[group_key] = {"group_key": dict(zip(grouping_fields, group_key)), "vm_count": 0, "vm_ids": []}

            groups[group_key]["vm_count"] += 1
            groups[group_key]["vm_ids"].append(analysis.vm_id)

        result = list(groups.values())
        logger.info(f"Generated {len(result)} migration groups")
        return result

    def apply_labels_from_analysis(
        self,
        convention_id: int,
        vm_filter: dict | None = None,
        overwrite_existing: bool = False,
        field_filter: list[str] | None = None,
        dry_run: bool = False,
        assigned_by: str = "naming_convention",
    ) -> dict[str, int]:
        """Apply labels to VMs based on naming convention field values.

        Creates labels with format: nc:<convention_name>:<field_name> = <field_value>

        Args:
            convention_id: ID of naming convention to process
            vm_filter: Optional filters for VMs (e.g., {'datacenter': 'DC1'})
            overwrite_existing: If True, replace existing labels with same key pattern
            field_filter: List of field names to process (None = all fields)
            dry_run: If True, don't actually create/apply labels, just return what would happen
            assigned_by: Username or system name assigning labels

        Returns:
            Dictionary with statistics:
            - labels_created: Number of new label definitions created
            - labels_assigned: Number of VM-label assignments created
            - vms_labeled: Number of unique VMs that received labels
            - labels_removed: Number of labels removed (if overwrite_existing)
            - labels_skipped: Number of label assignments skipped (already exist)

        Raises:
            NamingConventionError: If convention not found
        """
        logger.info(f"Applying labels from convention {convention_id}")

        convention = self.get_convention(convention_id)
        if not convention:
            raise NamingConventionError(f"Convention with ID {convention_id} not found")

        stats = {"labels_created": 0, "labels_assigned": 0, "vms_labeled": 0, "labels_removed": 0, "labels_skipped": 0}

        # Build query for valid analyses
        query = (
            self.session.query(VMNamingAnalysis, VirtualMachine)
            .join(VirtualMachine, VMNamingAnalysis.vm_id == VirtualMachine.id)
            .filter(VMNamingAnalysis.convention_id == convention_id, VMNamingAnalysis.is_valid.is_(True))
        )

        # Apply VM filters
        if vm_filter:
            for key, value in vm_filter.items():
                if hasattr(VirtualMachine, key):
                    query = query.filter(getattr(VirtualMachine, key) == value)

        analyses = query.all()

        if not analyses:
            logger.info("No valid analyses found to process")
            return stats

        logger.info(f"Processing {len(analyses)} valid VM analyses")

        # Determine which fields to process
        fields_to_process = convention.fields
        if field_filter:
            fields_to_process = [f for f in convention.fields if f.field_name in field_filter]

        if not fields_to_process:
            logger.warning("No fields to process")
            return stats

        # Track VMs that receive labels
        vms_labeled = set()

        # Process each analysis
        for analysis, vm in analyses:
            field_values = analysis.field_values

            # If overwrite_existing, remove old labels for this convention's fields
            if overwrite_existing and not dry_run:
                for field in fields_to_process:
                    label_key = f"nc:{convention.name}:{field.field_name}"
                    # Find and remove existing labels with this key
                    existing_label = self.session.query(Label).filter_by(key=label_key).first()
                    if existing_label:
                        vm_label = (
                            self.session.query(VMLabel).filter_by(vm_id=vm.id, label_id=existing_label.id).first()
                        )
                        if vm_label:
                            self.session.delete(vm_label)
                            stats["labels_removed"] += 1

            # Process each field
            for field in fields_to_process:
                field_value = field_values.get(field.field_name)

                # Skip empty or None values
                if not field_value:
                    continue

                # Generate label key and value
                label_key = f"nc:{convention.name}:{field.field_name}"
                label_value = str(field_value)

                # Get or create label definition
                label = self.session.query(Label).filter_by(key=label_key, value=label_value).first()

                if not label:
                    if dry_run:
                        stats["labels_created"] += 1
                    else:
                        # Create new label
                        label_description = f"Naming convention: {convention.name}, Field: {field.field_name}"
                        if field.description:
                            label_description += f" ({field.description})"

                        # Generate label name for display
                        label_name = f"{label_key} = {label_value}"

                        label = Label(
                            key=label_key,
                            value=label_value,
                            name=label_name,
                            category="naming_convention",
                            description=label_description,
                        )
                        self.session.add(label)
                        self.session.flush()  # Get ID
                        stats["labels_created"] += 1
                        logger.debug(f"Created label: {label_key}={label_value}")

                # Check if VM already has this label
                if not dry_run:
                    existing_assignment = self.session.query(VMLabel).filter_by(vm_id=vm.id, label_id=label.id).first()

                    if existing_assignment:
                        stats["labels_skipped"] += 1
                    else:
                        # Assign label to VM with source tracking
                        vm_label = VMLabel(
                            vm_id=vm.id,
                            label_id=label.id,
                            assigned_by=assigned_by,
                            inherited_from_folder=False,
                            label_source="naming_convention",
                            source_convention_id=convention_id,
                            source_field_name=field.field_name,
                            auto_created=True,
                        )
                        self.session.add(vm_label)
                        stats["labels_assigned"] += 1
                        logger.debug(f"Assigned label {label_key}={label_value} to VM {vm.vm}")
                else:
                    # In dry-run, just count potential assignments
                    stats["labels_assigned"] += 1

                vms_labeled.add(vm.id)

        stats["vms_labeled"] = len(vms_labeled)

        if not dry_run:
            self.session.commit()
            logger.info(f"Label application complete: {stats}")
        else:
            logger.info(f"Dry run complete (no changes made): {stats}")

        return stats

    def _validate_pattern_and_fields(self, pattern: str, fields: list[dict]) -> None:
        """Validate pattern and field definitions.

        Args:
            pattern: Pattern string
            fields: List of field definitions

        Raises:
            PatternValidationError: If validation fails
        """
        if not pattern:
            raise PatternValidationError("Pattern cannot be empty")

        if not fields:
            raise PatternValidationError("At least one field must be defined")

        # Check for duplicate positions
        positions = [f["position"] for f in fields]
        if len(positions) != len(set(positions)):
            raise PatternValidationError("Field positions must be unique")

        # Check for duplicate field names
        field_names = [f["field_name"] for f in fields]
        if len(field_names) != len(set(field_names)):
            raise PatternValidationError("Field names must be unique")

        # Validate field positions are consecutive starting from 0
        sorted_positions = sorted(positions)
        expected_positions = list(range(len(fields)))
        if sorted_positions != expected_positions:
            raise PatternValidationError(
                "Field positions must be consecutive starting from 0. "
                f"Expected {expected_positions}, got {sorted_positions}"
            )

        # Validate lengths are positive
        for field in fields:
            if field["length"] <= 0:
                raise PatternValidationError(f"Field '{field['field_name']}' length must be positive")
