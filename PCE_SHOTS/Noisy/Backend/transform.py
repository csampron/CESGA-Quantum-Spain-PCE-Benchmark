import os
import pandas as pd
import argparse
import json

def read_ibm_calibration_csv(name, directory="./"):
    file_name = next(
        (f for f in os.listdir(directory) if f.startswith(f"ibm_{name}_calibrations") and f.endswith(".csv")),
        None
    )
    if file_name is None:
        raise FileNotFoundError(f"No file starting with 'ibm_{name}_calibrations' and ending with '.csv' found in the directory {directory}.")
    file_path = os.path.join(directory, file_name)
    
    if os.path.exists(file_path):
        return pd.read_csv(file_path).to_dict(orient="records")
    else:
        raise FileNotFoundError(f"The file {file_name} does not exist in the directory {directory}.")


parser = argparse.ArgumentParser(description="Process IBM backend calibration data.")
parser.add_argument("ibm_backend", type=str, help="Name of the IBM backend.")
args = parser.parse_args()

ibm_backend = args.ibm_backend


calibration_csv = read_ibm_calibration_csv(ibm_backend)

gates_sq = ["Id", "Rz", "SX", "X"]
gates_tq = ["ECR"]

calibration_json = {
    "Qubits":{f"q[{k}]":{} for k in range(len(calibration_csv))},
    "Q1Gates":{f"q[{k}]":{j:{} for j in gates_sq} for k in range(len(calibration_csv))},
    "Q2Gates(RB)":{}
}

for q,qubit in enumerate(calibration_csv):

    calibration_json["Qubits"][f"q[{q}]"]["T1 (s)"] = qubit['T1 (us)']*1e-6
    calibration_json["Qubits"][f"q[{q}]"]["T2 (s)"] = qubit['T2 (us)']*1e-6
    calibration_json["Qubits"][f"q[{q}]"]["Drive Frequency (Hz)"] = qubit['Frequency (GHz)']
    calibration_json["Qubits"][f"q[{q}]"]["Readout duration (s)"] = qubit['Readout length (ns)']*1e-9
    calibration_json["Qubits"][f"q[{q}]"]["Readout fidelity (RB)"] = 1 - qubit['Readout assignment error ']



for q,qubit in enumerate(calibration_csv):

    # identity
    calibration_json["Q1Gates"][f"q[{q}]"]["Id"]["Gate duration (s)"] = 0
    calibration_json["Q1Gates"][f"q[{q}]"]["Id"]["Fidelity(RB)"] = 1 - qubit['ID error ']

    # rz
    calibration_json["Q1Gates"][f"q[{q}]"]["Rz"]["Gate duration (s)"] = 0
    calibration_json["Q1Gates"][f"q[{q}]"]["Rz"]["Fidelity(RB)"] = 1 - qubit['Z-axis rotation (rz) error ']

    # sx
    calibration_json["Q1Gates"][f"q[{q}]"]["SX"]["Gate duration (s)"] = 0
    calibration_json["Q1Gates"][f"q[{q}]"]["SX"]["Fidelity(RB)"] = 1 - qubit['√x (sx) error ']

    # x
    calibration_json["Q1Gates"][f"q[{q}]"]["X"]["Gate duration (s)"] = 0
    calibration_json["Q1Gates"][f"q[{q}]"]["X"]["Fidelity(RB)"] = 1 - qubit['Pauli-X error ']

cursed_qubits = []

for q,qubit in enumerate(calibration_csv):

    try:
        ecr_errors = qubit['ECR error '].split(';')  # Split by semicolon
        ecr_times = qubit['Gate time (ns)'].split(';')
        for error,time in zip(ecr_errors,ecr_times):
            pair, error = error.split(':')  # Split each entry into pair and fidelity
            pair, time = time.split(':')
            pair = pair.replace('_', '-')

            calibration_json["Q2Gates(RB)"][str(pair)] = {"ECR":{
                                                            "Control":int(pair.split('-')[0]),
                                                            "Target":int(pair.split('-')[1]),
                                                            "Duration (s)":float(time)*1e-9,
                                                            "Fidelity(RB)": 1 - float(error),
                                                            }}
    except Exception as error:
        print(error)
        cursed_qubits.append(q)

print(f"CURSED QUBITS FOR {ibm_backend}: ", cursed_qubits)

output_file = f"ibm_{ibm_backend}_calibrations.json"
with open(output_file, "w") as json_file:
    json.dump(calibration_json, json_file, indent=4)

print(f"Calibration data saved to {output_file}")