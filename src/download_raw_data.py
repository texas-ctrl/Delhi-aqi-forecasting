for station in ["anand_vihar", "rohini", "rk_puram", "punjabi_bagh", "ito", "okhla"]:
    print(station, os.listdir(f"../raw_data/{station}"))