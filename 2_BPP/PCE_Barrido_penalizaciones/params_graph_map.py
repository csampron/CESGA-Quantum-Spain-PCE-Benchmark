import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import re

def save_all_feasible_solutions(base_path, results_list):
    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)

    if not results_list:
        print("⚠️ No hay resultados para procesar")
        return

    df = pd.DataFrame(results_list)

    for m_val, group_m in df.groupby("m_val"):
        m_dir = base_path / f"m_{int(m_val)}"
        m_dir.mkdir(parents=True, exist_ok=True)

        total_count = int(len(group_m))
        feasible_count = int(group_m["feasible"].sum())
        ratio = float(feasible_count / total_count) if total_count > 0 else 0.0

        feasible = group_m[group_m["feasible"]]
        if feasible.empty:
            print(f"⚠️ No hay soluciones factibles para m_{m_val} (ratio {ratio:.2f})")
            continue

        grouped = feasible.groupby("min_bins")
        solutions_clean = []
        for min_bins_val, group in grouped:
            combos_clean = []
            for _, c in group.sort_values(["alpha", "A", "B", "D"]).iterrows():
                combos_clean.append({
                    "alpha": float(c["alpha"]),
                    "A": float(c["A"]),
                    "B": float(c["B"]),
                    "D": float(c["D"])
                })
            solutions_clean.append({
                "min_bins": int(min_bins_val),
                "combinations": combos_clean
            })

        json_path = m_dir / "all_feasible_solutions.json"
        with open(json_path, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "total_count": total_count,
                "feasible_count": feasible_count,
                "ratio_feasible": ratio,
                "solutions": solutions_clean
            }, f, indent=2)

        txt_path = m_dir / "all_feasible_solutions.txt"
        with open(txt_path, "w") as f:
            f.write(f"🎯 Todas las soluciones factibles para m_{int(m_val)}\n")
            f.write(f"Total ejecuciones: {total_count}, Factibles: {feasible_count}, Ratio: {ratio:.2f}\n\n")
            for sol in solutions_clean:
                f.write(f"min_bins = {sol['min_bins']}\n")
                for c in sol["combinations"]:
                    f.write(f"    alpha={c['alpha']}, A={c['A']}, B={c['B']}, D={c['D']}\n")
                f.write("\n")

        print(f"💾 Resumen para m_{int(m_val)} guardado (ratio factibles: {ratio:.2f}):\n  - {json_path}\n  - {txt_path}")

# =====================================
# Recopilar resultados
# =====================================
results_list = []
resultados_path = Path("/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/PCE_BPP_yj/PCE_Barrido_multi_qubits+1/Experimentos")

pattern = re.compile(r"alpha_(?P<alpha>[\d\.]+)_A_(?P<A>[\d\.]+)_B_(?P<B>[\d\.]+)_D_(?P<D>[\d\.]+)")

for m_folder in resultados_path.glob("m_*"):
    m_val = int(m_folder.name.split("_")[1])

    # Buscar k_* recursivamente en cualquier subcarpeta
    for k_folder in m_folder.rglob("k_*"):
        for ab_folder in k_folder.glob("alpha_*_A_*_B_*_D_*"):
            match = pattern.search(ab_folder.name)
            if match is None:
                continue

            alpha = float(match.group("alpha"))
            A = float(match.group("A"))
            B = float(match.group("B"))
            D = float(match.group("D"))

            res_dir = ab_folder / "Resultados"
            if not res_dir.exists():
                continue

            for jf in res_dir.glob("*.json"):
                with open(jf, "r") as f:
                    data = json.load(f)
                    for res in data.get("resultados", []):
                        feasible = res.get("feasibility_initial", {}).get("feasible", False)
                        min_bins = res.get("num_bins_used", None)
                        if min_bins is not None:
                            results_list.append({
                                "m_val": m_val,
                                "alpha": alpha,
                                "A": A,
                                "B": B,
                                "D": D,
                                "min_bins": min_bins,
                                "feasible": feasible
                            })

# Guardar resultados
save_all_feasible_solutions(
    "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/PCE_BPP_yj/PCE_Barrido_multi_qubits+1/Resumen_experimentos",
    results_list
)
