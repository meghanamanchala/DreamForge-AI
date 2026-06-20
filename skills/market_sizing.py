def compute_tam_sam_som(total_population, target_segment_percentage, penetration_rate, average_deal_size):
    """
    Decoupled business skill to compute standard startup market sizing matrices.
    - TAM = Total Population * Average Deal Size per Year
    - SAM = TAM * Target Segment Percentage (0.0 to 1.0)
    - SOM = SAM * Target Penetration Rate (0.0 to 1.0)
    """
    try:
        pop = float(total_population)
        segment = float(target_segment_percentage)
        penetration = float(penetration_rate)
        deal_size = float(average_deal_size)
    except (ValueError, TypeError):
        return {"error": "Invalid numerical parameters."}

    tam = pop * deal_size
    sam = tam * segment
    som = sam * penetration

    return {
        "tam": round(tam, 2),
        "sam": round(sam, 2),
        "som": round(som, 2)
    }
