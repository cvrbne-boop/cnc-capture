import React, { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader } from "@zxing/browser";

export default function Scanner() {
  const videoRef = useRef();
  const [result, setResult] = useState(null);
  const [operatorId, setOperatorId] = useState(1);
  const [machineId, setMachineId] = useState(1);

  useEffect(() => {
    const codeReader = new BrowserMultiFormatReader();
    let selectedDeviceId;

    codeReader
      .listVideoInputDevices()
      .then(videoInputDevices => {
        if (videoInputDevices.length > 0) {
          selectedDeviceId = videoInputDevices[0].deviceId;
          codeReader.decodeFromVideoDevice(selectedDeviceId, videoRef.current, (result, err) => {
            if (result) {
              setResult(result.getText());
              // send to backend
              fetch("/api/v1/scan", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({ operator_id: operatorId, machine_id: machineId, qr_payload: result.getText() })
              }).then(r=>r.json()).then(console.log).catch(console.error);
            }
          });
        }
      })
      .catch(err => console.error(err));

    return () => {
      codeReader.reset();
    };
  }, [operatorId, machineId]);

  return (
    <div>
      <h3>Scanner</h3>
      <div>
        Operator id: <input type="number" value={operatorId} onChange={e=>setOperatorId(+e.target.value)} />
        Machine id: <input type="number" value={machineId} onChange={e=>setMachineId(+e.target.value)} />
      </div>
      <video ref={videoRef} style={{width: "100%", maxWidth: 640}} />
      <div>Last QR: {result}</div>
    </div>
  );
}
