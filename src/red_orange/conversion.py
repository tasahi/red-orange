"""
Conversion layer between pandas DataFrames and Orange Tables.

This module is the **single gateway** through which data enters and exits
the headless widget engine.  Internally every widget works with
``Orange.data.Table``; externally the REST API speaks pandas / JSON.
The ``DomainSchema`` sidecar preserves column roles and variable types
across the boundary.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from Orange.data import (
    Table,
    Domain,
    ContinuousVariable,
    DiscreteVariable,
    StringVariable,
    TimeVariable,
)
from Orange.data.pandas_compat import table_from_frame, table_to_frame

from .schemas import ColumnSpec, DomainSchema, VarType


# ---------------------------------------------------------------------------
# Variable factories
# ---------------------------------------------------------------------------

_VAR_BUILDERS = {
    VarType.CONTINUOUS: lambda s: ContinuousVariable(
        s.name, number_of_decimals=s.number_of_decimals
    ),
    VarType.DISCRETE: lambda s: DiscreteVariable(
        s.name, values=tuple(s.values or ())
    ),
    VarType.TIME: lambda s: TimeVariable(s.name),
    VarType.STRING: lambda s: StringVariable(s.name),
}


def _make_variable(spec: ColumnSpec):
    """Create an Orange Variable from a ColumnSpec."""
    builder = _VAR_BUILDERS.get(spec.var_type)
    if builder is None:
        raise ValueError(f"Unknown variable type: {spec.var_type}")
    return builder(spec)


def _column_spec_from_variable(var) -> ColumnSpec:
    """Extract a ColumnSpec from an Orange Variable."""
    if var.is_discrete:
        return ColumnSpec(
            name=var.name,
            var_type=VarType.DISCRETE,
            values=list(var.values),
        )
    if var.is_time:
        return ColumnSpec(name=var.name, var_type=VarType.TIME)
    if var.is_continuous:
        return ColumnSpec(
            name=var.name,
            var_type=VarType.CONTINUOUS,
            number_of_decimals=var.number_of_decimals,
        )
    # StringVariable or unknown → string
    return ColumnSpec(name=var.name, var_type=VarType.STRING)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def dataframe_to_table(
    df: pd.DataFrame,
    schema: Optional[DomainSchema] = None,
) -> Table:
    """
    Convert a user-supplied pandas DataFrame into an ``Orange.data.Table``.

    If *schema* is ``None`` the column roles and types are auto-inferred by
    Orange's built-in ``table_from_frame``.  When a ``DomainSchema`` is
    provided the explicit role assignment (attributes / class_vars / metas)
    is honoured.

    Note: ``table_from_frame(variables=...)`` does **not** honour column roles
    — it always places everything in ``attributes``.  We therefore build the
    ``Domain`` ourselves and convert each column group independently.
    """
    if schema is None:
        return table_from_frame(df, force_nominal=False)

    import numpy as np

    attrs = [_make_variable(s) for s in schema.attributes]
    class_vars = [_make_variable(s) for s in schema.class_vars]
    metas = [_make_variable(s) for s in schema.metas]

    domain = Domain(attrs, class_vars, metas)

    def _series_to_array(var, series):
        """Convert a pandas Series to the numpy array Orange expects."""
        if var.is_discrete:
            codes = series.astype("category").cat.set_categories(
                var.values
            ).cat.codes.astype(float)
            codes[codes == -1] = float("nan")
            return codes.values
        if var.is_time:
            import pandas as _pd
            return (
                _pd.to_datetime(series, utc=True)
                .view("int64")
                .astype(float)
                / 1e9
            )
        if var.is_string:
            return series.astype(str).values.astype(object)
        return pd.to_numeric(series, errors="coerce").values

    # Build X (attributes)
    if attrs:
        X = np.column_stack(
            [_series_to_array(v, df[v.name]) for v in attrs]
        ).astype(float)
    else:
        X = np.empty((len(df), 0), dtype=float)

    # Build Y (class variables)
    if class_vars:
        if len(class_vars) == 1:
            Y = _series_to_array(class_vars[0], df[class_vars[0].name])
        else:
            Y = np.column_stack(
                [_series_to_array(v, df[v.name]) for v in class_vars]
            ).astype(float)
    else:
        Y = None

    # Build metas
    if metas:
        M = np.column_stack(
            [_series_to_array(v, df[v.name]) for v in metas]
        ).astype(object)
    else:
        M = None

    return Table.from_numpy(domain, X, Y, metas=M)


def table_to_dataframe(
    table: Table,
) -> tuple[pd.DataFrame, DomainSchema]:
    """
    Convert an ``Orange.data.Table`` to a pandas DataFrame together with a
    ``DomainSchema`` sidecar that records which columns are attributes,
    targets and metas.
    """
    df = table_to_frame(table, include_metas=True)

    schema = DomainSchema(
        attributes=[
            _column_spec_from_variable(v) for v in table.domain.attributes
        ],
        class_vars=[
            _column_spec_from_variable(v) for v in table.domain.class_vars
        ],
        metas=[
            _column_spec_from_variable(v) for v in table.domain.metas
        ],
    )
    return df, schema
