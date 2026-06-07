import streamlit as st
from data.datatypes import (
    LandSupplyZone, RiverSupplyCorridor, CoastalSupplyZone,
    SoilType, RotationSystem
    )
import pandas as pd

with st.container(horizontal=True):
    st.write("# Step 1: Supply Zone")

    miles_water = st.number_input("Miles of navigable water:", min_value=0)
    coast_area = st.number_input("Coastal square miles:", min_value=0, step=10)

    land_supply = LandSupplyZone()
    river_supply = RiverSupplyCorridor(miles_water)
    coastal_supply = CoastalSupplyZone(coast_area)
    total_supply_area = int(land_supply.hectares + river_supply.hectares + coastal_supply.hectares)

    data = {
        "Supply zone" : ["Land-only", "River supply", "Coastal", "Subtotal"],
        "Max hectares" : [int(land_supply.hectares), int(river_supply.hectares), int(coastal_supply.hectares),
                          total_supply_area],
    }
    st.table(data, border='horizontal')

with st.container():
    st.write("# Step 2: Classify the Soil")

    df = pd.DataFrame(
    [
        {"name": "Golden Zone", "description": "River deltas and floodplains", "plot_size" : 6,
         "yield_ratio": 8, "arable": "80"},
        {"name": "Rich lowland", "description": "Flat, temperate plains", "plot_size" : 12, 
         "yield_ratio": 4, "arable": "60"},
        {"name": "Stubborn Frontier", "description": "Heavy Clay, Deep midlands and dense continental interiors", 
         "plot_size": 12, "yield_ratio": 3, "arable": "40"},
        {"name": "Fraying Edges", "description": "Chalk/Sand. Arid scrublands coastal plains and limestone hills", 
         "plot_size" : 12, "yield_ratio": 2, "arable": "20"},
    ]
    )
    edited_df = st.data_editor(df, 
                               num_rows="dynamic",
                               hide_index= True,
                               column_config={
                                   "arable" : st.column_config.NumberColumn(
                                       help="Percentage of the soil that is arable",
                                       min_value=0,
                                       max_value=100,
                                       format="%.0f%%"
                                   ),
                                   "yield_ratio" : st.column_config.NumberColumn(
                                       help="How many buckets of grain would grow per bucket planted",
                                       min_value=0,
                                       max_value=100,
                                       format="%d/1"
                                   )
                               })

    soiltypes = []
    for i,r in edited_df.iterrows():
        soiltypes.append(SoilType(**r.to_dict()))    

    st.selectbox("Soiltype", soiltypes)

with st.container(horizontal=True):
    st.write("# Step 3: Apply maritime modifier")
    fisheries = st.checkbox("Does your city have fisheries?")
    salt_supply = st.checkbox("Does it have the salt supply needed to preserve and distribute the fish?")

with st.container():
    st.write("# Step 4 : Calculate the Real Agricultural Footprint")

    footprint_per_area = pd.DataFrame(
        [{
            "zone": s.name,
            "total_area" : 0,
            "arable_area" : s.arable,
            } for s in soiltypes]
        )

    edited_footprint_per_area = st.data_editor(
        footprint_per_area[["zone","total_area"]],
        hide_index= True,
        disabled=["zone"],
        column_config={
            "total_area" : st.column_config.NumberColumn(
            help="Percentage of the soil that is arable",
            min_value=0,
            max_value=total_supply_area,
            step=1000
            )
        }
    )
    edited_footprint_per_area["effective_area"] = (footprint_per_area["arable_area"].astype(float)/100) * edited_footprint_per_area["total_area"].astype(float) # * edited_footprint_per_area["total_area"]
    total_allocated = edited_footprint_per_area["total_area"].sum()

    if total_allocated > total_supply_area:
        st.error(
            f"Total allocated area ({total_allocated:,.0f}) exceeds "
            f"available supply area ({total_supply_area:,.0f})."
        )
    else:
        available_supply_area = total_supply_area - total_allocated
        st.success(f"Remaining area: {available_supply_area:,.0f}")

        st.dataframe(edited_footprint_per_area)

        st.info(f"Total effective area: {edited_footprint_per_area.effective_area.sum():,.0f}")


        with st.container():
            #st.write("# Step 5 : Apply Technology Modifiers (Optional)") -> later

            st.write("# Step 6 : Count the Families")

            fam_df = edited_df.set_index("name")[["plot_size"]].join(
              edited_footprint_per_area.set_index("zone")[["effective_area"]]
            )

            fam_df["total_farming_families"] = fam_df["effective_area"] / fam_df["plot_size"]
            fam_df["total_rural_population"] = 5 * fam_df["total_farming_families"]
            fam_df.loc["Total", "total_rural_population"] = fam_df["total_rural_population"].sum()
             
            st.dataframe(fam_df)

        with st.container():
            st.write("# Step 7 : Choose Your Rotation System")

            rot_systems = [
                RotationSystem("Two-field system", 1/2),
                RotationSystem("Three-field system", 2/3),
                RotationSystem("Floodplain", 1)
            ]

            rotation_system_used = st.selectbox("Select the rotation system used", rot_systems)

        with st.container():
            st.write("# Step 8 : Calculate Your Surplus Grain")

            lord_tithe = st.number_input("Lord's tithe (%)", 
                            min_value=0, max_value=100, 
                            icon="👑", format="%d",
                            value = 15
                            ) / 100

            s = fam_df.drop("Total").join(
                df.set_index("name")["yield_ratio"]
            )
            
            s["gross_harvest"] = s["yield_ratio"]* 6 * s["total_farming_families"] * \
                (rotation_system_used.modifier * s["plot_size"])
            
            s["lord_extraction"] = (1-lord_tithe) * s["gross_harvest"]
            s["church_tithe"] = .9 * s["lord_extraction"]
            s["spoilage"] = .8 * s["church_tithe"]
            s["seed_bank"] = 6 * s["total_farming_families"] * s["plot_size"]
            s["peasant_subsistence"] = s["spoilage"] - s["seed_bank"] - (s["total_farming_families"] * 40)
            s["raw_surplus"] = (0.2 * s["lord_extraction"]) + s["peasant_subsistence"]
            s["town_cut"] = .8 * s["raw_surplus"]

            st.dataframe(
                s[["gross_harvest", "lord_extraction", "church_tithe", 
                   "spoilage", "seed_bank", "peasant_subsistence", "raw_surplus",
                   "town_cut"]]
                )
            
            total_exportable = s['town_cut'].sum()
            st.info(f"Total exportable surplus: {total_exportable:,.0f}")

        with st.container(horizontal=True):
            st.write("# Step 9 : The Grain's Journey")
            dist_granary = st.number_input("Average distance to barn in miles", min_value=2, max_value=5, value=3)
            grain_journey = (1 - (.002 * dist_granary)) * total_exportable  
            dist_collection = st.number_input("Average distance to collection point in miles", min_value=2, max_value=5, value=3)
            grain_journey = (1 - (.002 * dist_collection)) * grain_journey * .96
            # tolls
            num_road_bridge = st.number_input("Average number of roads/bridges", value=2)
            num_river_town = st.number_input("Average number of river town crossings", value=1)
            major_port = st.checkbox("Major port en route")
            
            grain_journey = (.99 ** num_road_bridge * .97 ** num_river_town) * grain_journey
            if major_port:
                grain_journey = .96 * grain_journey
                grain_journey = .95 * grain_journey
            
            grain_journey = grain_journey * .85

            st.info(f"Grain surviving the journey: {grain_journey:,.0f}", icon="🌾")

            max_population = grain_journey / (10 - 2*fisheries*salt_supply)

            st.info(f"Max city population: {max_population:,.0f}", icon="👥")
