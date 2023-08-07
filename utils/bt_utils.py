import streamlit as st


def get_strategy_config_fields_and_values(fields: dict, trial_config: dict):
    """Overrides st.session_state.strategy_params, later used in strategy instantiation for run_backtesting method"""
    container = st.container()
    with container:
        c1, c2 = st.columns([5, 1])
        with c1:
            columns = st.columns(4)
            column_index = 0
            for field_name, properties in fields.items():
                field_type = properties["type"]
                field_value = trial_config[field_name]
                with columns[column_index]:
                    if field_type in ["number", "integer"]:
                        field_value = st.number_input(field_name,
                                                      value=field_value,
                                                      min_value=properties.get("minimum"),
                                                      max_value=properties.get("maximum"),
                                                      key=field_name)
                    elif field_type == "string":
                        field_value = st.text_input(field_name, value=field_value)
                    elif field_type == "boolean":
                        # TODO: Add support for boolean fields in optimize tab
                        field_value = st.checkbox(field_name, value=field_value)
                    else:
                        raise ValueError(f"Field type {field_type} not supported")
                    try:
                        st.session_state["strategy_params"][field_name] = field_value
                    except KeyError as e:
                        pass
                column_index = (column_index + 1) % 4
        with c2:
            add_positions = st.checkbox("Add positions", value=True)
            add_volume = st.checkbox("Add volume", value=True)
            add_pnl = st.checkbox("Add PnL", value=True)
    return container, add_pnl, add_volume, add_positions
