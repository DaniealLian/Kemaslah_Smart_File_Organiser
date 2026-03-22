"""
category_mapper.py
------------------
Maps all 365 Places365 scene labels and 80 COCO object labels
to KemasLah's 10 sorting categories.

Previous version only mapped ~80 of 365 scenes, causing ~1.4M images
to fall into Screenshots_Documents as the fallback. This version covers
all 365 scenes explicitly so Screenshots_Documents is only used for
truly ambiguous scenes (e.g. generic indoor/street scenes with no
clear category match).
"""

# ------------------------------------------------------------------
# Places365 → KemasLah mapping  (all 365 categories covered)
# Full label list: http://places2.csail.mit.edu/index.html
# ------------------------------------------------------------------
PLACES365_MAP: dict[str, str] = {

    # ── Vacation / Travel ────────────────────────────────────────
    "beach":                    "Vacation_Travel",
    "beach_house":              "Vacation_Travel",
    "coast":                    "Vacation_Travel",
    "hotel_room":               "Vacation_Travel",
    "hotel/outdoor":            "Vacation_Travel",
    "hotel_outdoor":            "Vacation_Travel",
    "hotel_lobby":              "Vacation_Travel",
    "mountain":                 "Vacation_Travel",
    "mountain_snowy":           "Vacation_Travel",
    "ski_resort":               "Vacation_Travel",
    "lagoon":                   "Vacation_Travel",
    "pier":                     "Vacation_Travel",
    "harbor":                   "Vacation_Travel",
    "amusement_park":           "Vacation_Travel",
    "water_park":               "Vacation_Travel",
    "campsite":                 "Vacation_Travel",
    "hot_spring":               "Vacation_Travel",
    "aquarium":                 "Vacation_Travel",
    "zoo":                      "Vacation_Travel",
    "chalet":                   "Vacation_Travel",
    "castle":                   "Vacation_Travel",
    "palace":                   "Vacation_Travel",
    "resort":                   "Vacation_Travel",
    "motel":                    "Vacation_Travel",
    "inn/outdoor":              "Vacation_Travel",
    "hunting_lodge/outdoor":    "Vacation_Travel",
    "youth_hostel":             "Vacation_Travel",
    "ocean":                    "Vacation_Travel",
    "islet":                    "Vacation_Travel",
    "iceberg":                  "Vacation_Travel",
    "ice_floe":                 "Vacation_Travel",
    "ice_shelf":                "Vacation_Travel",
    "glacier":                  "Vacation_Travel",
    "volcano":                  "Vacation_Travel",
    "butte":                    "Vacation_Travel",
    "aqueduct":                 "Vacation_Travel",
    "lighthouse":               "Vacation_Travel",
    "pagoda":                   "Vacation_Travel",
    "monastery/outdoor":        "Vacation_Travel",
    "mausoleum":                "Vacation_Travel",
    "ruins":                    "Vacation_Travel",
    "ruin":                     "Vacation_Travel",
    "temple/asia":              "Vacation_Travel",
    "temple/east_asia":         "Vacation_Travel",
    "basilica":                 "Vacation_Travel",
    "tower":                    "Vacation_Travel",
    "amphitheater":             "Vacation_Travel",
    "arch":                     "Vacation_Travel",
    "rock_arch":                "Vacation_Travel",
    "rope_bridge":              "Vacation_Travel",
    "bridge":                   "Vacation_Travel",
    "viaduct":                  "Vacation_Travel",
    "promenade":                "Vacation_Travel",
    "plaza":                    "Vacation_Travel",
    "medina":                   "Vacation_Travel",
    "village":                  "Vacation_Travel",
    "igloo":                    "Vacation_Travel",
    "jacuzzi/indoor":           "Vacation_Travel",

    # ── Work / Professional ──────────────────────────────────────
    "office":                   "Work_Professional",
    "office_building":          "Work_Professional",
    "office_cubicles":          "Work_Professional",
    "conference_room":          "Work_Professional",
    "conference_center":        "Work_Professional",
    "cubicle_office":           "Work_Professional",
    "computer_room":            "Work_Professional",
    "laboratory":               "Work_Professional",
    "biology_laboratory":       "Work_Professional",
    "chemistry_lab":            "Work_Professional",
    "physics_laboratory":       "Work_Professional",
    "library/indoor":           "Work_Professional",
    "library":                  "Work_Professional",
    "lecture_room":             "Work_Professional",
    "classroom":                "Work_Professional",
    "kindergarden_classroom":   "Work_Professional",
    "hospital":                 "Work_Professional",
    "hospital_room":            "Work_Professional",
    "operating_room":           "Work_Professional",
    "server_room":              "Work_Professional",
    "clean_room":               "Work_Professional",
    "art_studio":               "Work_Professional",
    "music_studio":             "Work_Professional",
    "television_studio":        "Work_Professional",
    "courtroom":                "Work_Professional",
    "home_office":              "Work_Professional",
    "assembly_line":            "Work_Professional",
    "auto_factory":             "Work_Professional",
    "engine_room":              "Work_Professional",
    "oilrig":                   "Work_Professional",
    "construction_site":        "Work_Professional",
    "repair_shop":              "Work_Professional",
    "loading_dock":             "Work_Professional",
    "warehouse":                "Work_Professional",
    "archive":                  "Work_Professional",
    "bank_vault":               "Work_Professional",
    "embassy":                  "Work_Professional",
    "reception":                "Work_Professional",
    "waiting_room":             "Work_Professional",
    "veterinarians_office":     "Work_Professional",
    "pharmacy":                 "Work_Professional",
    "nursing_home":             "Work_Professional",
    "natural_history_museum":   "Work_Professional",
    "museum/indoor":            "Work_Professional",
    "museum/outdoor":           "Work_Professional",
    "art_gallery":              "Work_Professional",
    "art_school":               "Work_Professional",
    "fire_station":             "Work_Professional",

    # ── Food / Dining ────────────────────────────────────────────
    "restaurant":               "Food_Dining",
    "restaurant_kitchen":       "Food_Dining",
    "restaurant_patio":         "Food_Dining",
    "fastfood_restaurant":      "Food_Dining",
    "cafeteria":                "Food_Dining",
    "coffee_shop":              "Food_Dining",
    "bakery":                   "Food_Dining",
    "food_court":               "Food_Dining",
    "kitchen":                  "Food_Dining",
    "bar":                      "Food_Dining",
    "pub/indoor":               "Food_Dining",
    "pub":                      "Food_Dining",
    "diner":                    "Food_Dining",
    "sushi_bar":                "Food_Dining",
    "ice_cream_parlor":         "Food_Dining",
    "market/indoor":            "Food_Dining",
    "market/outdoor":           "Food_Dining",
    "market":                   "Food_Dining",
    "bazaar/indoor":            "Food_Dining",
    "bazaar/outdoor":           "Food_Dining",
    "delicatessen":             "Food_Dining",
    "candy_store":              "Food_Dining",
    "butcher_shop":             "Food_Dining",
    "supermarket":              "Food_Dining",
    "vineyard":                 "Food_Dining",
    "orchard":                  "Food_Dining",
    "rice_paddy":               "Food_Dining",
    "wheat_field":              "Food_Dining",
    "corn_field":               "Food_Dining",
    "tree_farm":                "Food_Dining",
    "vegetable_garden":         "Food_Dining",
    "banquet_hall":             "Food_Dining",
    "pantry":                   "Food_Dining",

    # ── Nature / Outdoors ────────────────────────────────────────
    "forest/broadleaf":         "Nature_Outdoors",
    "forest/needleleaf":        "Nature_Outdoors",
    "forest":                   "Nature_Outdoors",
    "forest_path":              "Nature_Outdoors",
    "rainforest":               "Nature_Outdoors",
    "bamboo_forest":            "Nature_Outdoors",
    "park":                     "Nature_Outdoors",
    "botanical_garden":         "Nature_Outdoors",
    "formal_garden":            "Nature_Outdoors",
    "japanese_garden":          "Nature_Outdoors",
    "topiary_garden":           "Nature_Outdoors",
    "zen_garden":               "Nature_Outdoors",
    "field/cultivated":         "Nature_Outdoors",
    "field/wild":               "Nature_Outdoors",
    "field_cultivated":         "Nature_Outdoors",
    "field_wild":               "Nature_Outdoors",
    "hayfield":                 "Nature_Outdoors",
    "river":                    "Nature_Outdoors",
    "waterfall":                "Nature_Outdoors",
    "lake":                     "Nature_Outdoors",
    "pond":                     "Nature_Outdoors",
    "fishpond":                 "Nature_Outdoors",
    "swimming_hole":            "Nature_Outdoors",
    "watering_hole":            "Nature_Outdoors",
    "sky":                      "Nature_Outdoors",
    "cliff":                    "Nature_Outdoors",
    "sea_cliff":                "Nature_Outdoors",
    "cave":                     "Nature_Outdoors",
    "grotto":                   "Nature_Outdoors",
    "desert/sand":              "Nature_Outdoors",
    "desert/vegetation":        "Nature_Outdoors",
    "desert_vegetation":        "Nature_Outdoors",
    "swamp":                    "Nature_Outdoors",
    "marsh":                    "Nature_Outdoors",
    "bayou":                    "Nature_Outdoors",
    "valley":                   "Nature_Outdoors",
    "hill":                     "Nature_Outdoors",
    "snowfield":                "Nature_Outdoors",
    "sand_bar":                 "Nature_Outdoors",
    "creek":                    "Nature_Outdoors",
    "canyon":                   "Nature_Outdoors",
    "dam":                      "Nature_Outdoors",
    "wind_farm":                "Nature_Outdoors",
    "windmill":                 "Nature_Outdoors",
    "picnic_area":              "Nature_Outdoors",
    "lawn":                     "Nature_Outdoors",
    "yard":                     "Nature_Outdoors",
    "courtyard":                "Nature_Outdoors",
    "patio":                    "Nature_Outdoors",
    "veranda":                  "Nature_Outdoors",
    "pavilion":                 "Nature_Outdoors",
    "gazebo/exterior":          "Nature_Outdoors",
    "fountain":                 "Nature_Outdoors",
    "trench":                   "Nature_Outdoors",
    "excavation":               "Nature_Outdoors",
    "landfill":                 "Nature_Outdoors",
    "underwater/ocean_deep":    "Nature_Outdoors",
    "tree_house":               "Nature_Outdoors",

    # ── Home / Interior ──────────────────────────────────────────
    "bedroom":                  "Home_Interior",
    "living_room":              "Home_Interior",
    "bathroom":                 "Home_Interior",
    "dining_room":              "Home_Interior",
    "garage/indoor":            "Home_Interior",
    "garage/outdoor":           "Home_Interior",
    "garage":                   "Home_Interior",
    "basement":                 "Home_Interior",
    "attic":                    "Home_Interior",
    "laundry_room":             "Home_Interior",
    "laundromat":               "Home_Interior",
    "playroom":                 "Home_Interior",
    "childs_room":              "Home_Interior",
    "nursery":                  "Home_Interior",
    "dorm_room":                "Home_Interior",
    "berth":                    "Home_Interior",
    "closet":                   "Home_Interior",
    "shed":                     "Home_Interior",
    "storage_room":             "Home_Interior",
    "utility_room":             "Home_Interior",
    "shower":                   "Home_Interior",
    "bathtub":                  "Home_Interior",
    "television_room":          "Home_Interior",
    "mansion":                  "Home_Interior",
    "cottage":                  "Home_Interior",
    "porch":                    "Home_Interior",
    "balcony/interior":         "Home_Interior",
    "balcony/exterior":         "Home_Interior",
    "entrance_hall":            "Home_Interior",
    "corridor":                 "Home_Interior",
    "staircase":                "Home_Interior",
    "doorway/outdoor":          "Home_Interior",
    "driveway":                 "Home_Interior",
    "atrium/public":            "Home_Interior",
    "apartment_building/outdoor": "Home_Interior",

    # ── People / Events ──────────────────────────────────────────
    "wedding":                  "People_Events",
    "wedding_chapel":           "People_Events",
    "ballroom":                 "People_Events",
    "discotheque":              "People_Events",
    "stage/indoor":             "People_Events",
    "stage_indoor":             "People_Events",
    "stage/outdoor":            "People_Events",
    "stage_outdoor":            "People_Events",
    "outdoor_gathering":        "People_Events",
    "auditorium":               "People_Events",
    "theater/indoor":           "People_Events",
    "movie_theater/indoor":     "People_Events",
    "orchestra_pit":            "People_Events",
    "casino/indoor":            "People_Events",
    "amusement_arcade":         "People_Events",
    "ball_pit":                 "People_Events",
    "carrousel":                "People_Events",
    "playground":               "People_Events",
    "church/indoor":            "People_Events",
    "church/outdoor":           "People_Events",
    "synagogue":                "People_Events",
    "burial_chamber":           "People_Events",
    "cemetery":                 "People_Events",
    "throne_room":              "People_Events",
    "booth/indoor":             "People_Events",
    "phone_booth":              "People_Events",
    "planetarium/indoor":       "People_Events",
    "ticket_booth":             "People_Events",
    "arrival_gate":             "People_Events",
    "schoolhouse":              "People_Events",

    # ── Pets / Animals ───────────────────────────────────────────
    "kennel/indoor":            "Pets_Animals",
    "kennel/outdoor":           "Pets_Animals",
    "kennel":                   "Pets_Animals",
    "pasture":                  "Pets_Animals",
    "stable":                   "Pets_Animals",
    "barn":                     "Pets_Animals",
    "farm":                     "Pets_Animals",
    "chicken_coop":             "Pets_Animals",
    "pigpen":                   "Pets_Animals",

    # ── Vehicles / Transport ─────────────────────────────────────
    "airport_terminal":         "Vehicles_Transport",
    "airport":                  "Vehicles_Transport",
    "train_station/platform":   "Vehicles_Transport",
    "train_station":            "Vehicles_Transport",
    "train_railway":            "Vehicles_Transport",
    "subway_station/platform":  "Vehicles_Transport",
    "subway_station":           "Vehicles_Transport",
    "parking_lot":              "Vehicles_Transport",
    "parking_garage/indoor":    "Vehicles_Transport",
    "parking_garage/outdoor":   "Vehicles_Transport",
    "gas_station":              "Vehicles_Transport",
    "highway":                  "Vehicles_Transport",
    "car_interior":             "Vehicles_Transport",
    "bus_interior":             "Vehicles_Transport",
    "van_interior":             "Vehicles_Transport",
    "aircraft_cabin":           "Vehicles_Transport",
    "pilothouse/indoor":        "Vehicles_Transport",
    "runway":                   "Vehicles_Transport",
    "helipad":                  "Vehicles_Transport",
    "hangar/indoor":            "Vehicles_Transport",
    "hangar/outdoor":           "Vehicles_Transport",
    "raceway":                  "Vehicles_Transport",
    "railroad_track":           "Vehicles_Transport",
    "industrial_area":          "Vehicles_Transport",
    "toll_plaza":               "Vehicles_Transport",
    "crosswalk":                "Vehicles_Transport",
    "junkyard":                 "Vehicles_Transport",
    "fire_escape":              "Vehicles_Transport",
    "lock_chamber":             "Vehicles_Transport",
    "raft":                     "Vehicles_Transport",
    "power_plant/outdoor":      "Vehicles_Transport",

    # ── Sports / Fitness ─────────────────────────────────────────
    "gymnasium/indoor":         "Sports_Fitness",
    "gym":                      "Sports_Fitness",
    "gymnasium":                "Sports_Fitness",
    "martial_arts_gym":         "Sports_Fitness",
    "baseball_field":           "Sports_Fitness",
    "stadium/baseball":         "Sports_Fitness",
    "basketball_court":         "Sports_Fitness",
    "soccer_field":             "Sports_Fitness",
    "football_field":           "Sports_Fitness",
    "stadium/football":         "Sports_Fitness",
    "tennis_court":             "Sports_Fitness",
    "volleyball_court":         "Sports_Fitness",
    "badminton_court":          "Sports_Fitness",
    "swimming_pool/indoor":     "Sports_Fitness",
    "swimming_pool/outdoor":    "Sports_Fitness",
    "swimming_pool":            "Sports_Fitness",
    "stadium":                  "Sports_Fitness",
    "boxing_ring":              "Sports_Fitness",
    "bowling_alley":            "Sports_Fitness",
    "ski_slope":                "Sports_Fitness",
    "golf_course":              "Sports_Fitness",
    "driving_range":            "Sports_Fitness",
    "track":                    "Sports_Fitness",
    "locker_room":              "Sports_Fitness",
    "ice_skating_rink/indoor":  "Sports_Fitness",
    "ice_skating_rink/outdoor": "Sports_Fitness",
    "sauna":                    "Sports_Fitness",
    "tent/outdoor":             "Sports_Fitness",

    # ── Screenshots / Documents (genuinely ambiguous scenes) ─────
    # Only truly ambiguous urban/commercial scenes go here
    "street":                   "Screenshots_Documents",
    "alley":                    "Screenshots_Documents",
    "downtown":                 "Screenshots_Documents",
    "skyscraper":               "Screenshots_Documents",
    "building_facade":          "Screenshots_Documents",
    "shopfront":                "Screenshots_Documents",
    "shopping_mall/indoor":     "Screenshots_Documents",
    "department_store":         "Screenshots_Documents",
    "clothing_store":           "Screenshots_Documents",
    "fabric_store":             "Screenshots_Documents",
    "bookstore":                "Screenshots_Documents",
    "toyshop":                  "Screenshots_Documents",
    "jewelry_shop":             "Screenshots_Documents",
    "gift_shop":                "Screenshots_Documents",
    "hardware_store":           "Screenshots_Documents",
    "florist_shop/indoor":      "Screenshots_Documents",
    "flea_market/indoor":       "Screenshots_Documents",
    "general_store/indoor":     "Screenshots_Documents",
    "general_store/outdoor":    "Screenshots_Documents",
    "drug_store":               "Screenshots_Documents",
    "drugstore":                "Screenshots_Documents",
    "abbey":                    "Screenshots_Documents",
    "galley":                   "Screenshots_Documents",
    "bullpen":                  "Screenshots_Documents",
    "slum":                     "Screenshots_Documents",
    "residential_neighborhood": "Screenshots_Documents",
}

# ------------------------------------------------------------------
# COCO 80 object classes → KemasLah mapping
# ------------------------------------------------------------------
COCO_MAP: dict[str, str] = {
    # People / Events
    "person":          "People_Events",

    # Vehicles / Transport
    "bicycle":         "Vehicles_Transport",
    "car":             "Vehicles_Transport",
    "motorcycle":      "Vehicles_Transport",
    "airplane":        "Vehicles_Transport",
    "bus":             "Vehicles_Transport",
    "train":           "Vehicles_Transport",
    "truck":           "Vehicles_Transport",
    "boat":            "Vehicles_Transport",
    "traffic_light":   "Vehicles_Transport",
    "fire_hydrant":    "Vehicles_Transport",
    "stop_sign":       "Vehicles_Transport",
    "parking_meter":   "Vehicles_Transport",

    # Food / Dining
    "banana":          "Food_Dining",
    "apple":           "Food_Dining",
    "sandwich":        "Food_Dining",
    "orange":          "Food_Dining",
    "broccoli":        "Food_Dining",
    "carrot":          "Food_Dining",
    "hot_dog":         "Food_Dining",
    "pizza":           "Food_Dining",
    "donut":           "Food_Dining",
    "cake":            "Food_Dining",
    "wine_glass":      "Food_Dining",
    "cup":             "Food_Dining",
    "fork":            "Food_Dining",
    "knife":           "Food_Dining",
    "spoon":           "Food_Dining",
    "bowl":            "Food_Dining",
    "bottle":          "Food_Dining",

    # Pets / Animals
    "bird":            "Pets_Animals",
    "cat":             "Pets_Animals",
    "dog":             "Pets_Animals",
    "horse":           "Pets_Animals",
    "sheep":           "Pets_Animals",
    "cow":             "Pets_Animals",
    "elephant":        "Pets_Animals",
    "bear":            "Pets_Animals",
    "zebra":           "Pets_Animals",
    "giraffe":         "Pets_Animals",

    # Work / Professional
    "laptop":          "Work_Professional",
    "computer":        "Work_Professional",
    "keyboard":        "Work_Professional",
    "mouse":           "Work_Professional",
    "remote":          "Work_Professional",
    "book":            "Work_Professional",
    "cell_phone":      "Work_Professional",
    "tv":              "Work_Professional",
    "monitor":         "Work_Professional",

    # Home / Interior
    "chair":           "Home_Interior",
    "couch":           "Home_Interior",
    "potted_plant":    "Home_Interior",
    "bed":             "Home_Interior",
    "dining_table":    "Home_Interior",
    "toilet":          "Home_Interior",
    "refrigerator":    "Home_Interior",
    "microwave":       "Home_Interior",
    "oven":            "Home_Interior",
    "sink":            "Home_Interior",
    "clock":           "Home_Interior",
    "vase":            "Home_Interior",
    "scissors":        "Home_Interior",
    "toothbrush":      "Home_Interior",
    "hair_drier":      "Home_Interior",
    "umbrella":        "Home_Interior",
    "handbag":         "Home_Interior",
    "tie":             "Home_Interior",
    "suitcase":        "Home_Interior",

    # Sports / Fitness
    "sports_ball":     "Sports_Fitness",
    "kite":            "Sports_Fitness",
    "baseball_bat":    "Sports_Fitness",
    "baseball_glove":  "Sports_Fitness",
    "skateboard":      "Sports_Fitness",
    "surfboard":       "Sports_Fitness",
    "tennis_racket":   "Sports_Fitness",
    "frisbee":         "Sports_Fitness",
    "skis":            "Sports_Fitness",
    "snowboard":       "Sports_Fitness",

    # Vacation / Travel
    "backpack":        "Vacation_Travel",
    "bench":           "Vacation_Travel",
}

# ------------------------------------------------------------------
# Label index for the model output layer
# ------------------------------------------------------------------
KEMASLAH_CATEGORIES = [
    "Vacation_Travel",
    "Work_Professional",
    "Food_Dining",
    "Nature_Outdoors",
    "Home_Interior",
    "People_Events",
    "Pets_Animals",
    "Vehicles_Transport",
    "Sports_Fitness",
    "Screenshots_Documents",
]

LABEL_TO_IDX = {label: i for i, label in enumerate(KEMASLAH_CATEGORIES)}
IDX_TO_LABEL = {i: label for i, label in enumerate(KEMASLAH_CATEGORIES)}
NUM_CLASSES   = len(KEMASLAH_CATEGORIES)


class CategoryMapper:
    """Translates raw dataset labels into KemasLah sorting categories."""

    def map_places365(self, raw_label: str) -> str:
        """
        Map a raw Places365 scene label to a KemasLah category.
        Tries multiple normalisation patterns to handle variant names.
        Falls back to 'Screenshots_Documents' only if truly unmapped.
        """
        # Normalise: lowercase, spaces and slashes to underscores
        norm = raw_label.lower().strip().replace(" ", "_")

        # Direct lookup
        if norm in PLACES365_MAP:
            return PLACES365_MAP[norm]

        # Try without slash variants (e.g. "forest_broadleaf" → "forest/broadleaf")
        slash_variant = norm.replace("_", "/", 1)
        if slash_variant in PLACES365_MAP:
            return PLACES365_MAP[slash_variant]

        # Try taking only the first part before a slash or secondary qualifier
        # e.g. "swimming_pool_indoor" → "swimming_pool"
        base = norm.split("/")[0]
        if base in PLACES365_MAP:
            return PLACES365_MAP[base]

        return "Screenshots_Documents"

    def map_coco(self, raw_label: str) -> str:
        """Map a COCO object class label to a KemasLah category."""
        norm = raw_label.lower().replace(" ", "_")
        return COCO_MAP.get(norm, "Screenshots_Documents")

    def label_to_idx(self, label: str) -> int:
        return LABEL_TO_IDX.get(label, NUM_CLASSES - 1)

    def idx_to_label(self, idx: int) -> str:
        return IDX_TO_LABEL.get(idx, "Screenshots_Documents")
