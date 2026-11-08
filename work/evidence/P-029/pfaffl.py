import pandas as pd
import qpcr

analyser = qpcr.Analyser()
analyser.anchor("first")
processed = []
for gene, factor, control, sample in [
    ("TyrA", 2.09, 20.303, 15.020),
    ("Gst", 1.99, 14.277, 14.533),
]:
    frame = pd.DataFrame({"id": ["control", "sample"], "Ct": [control, sample]})
    assay = qpcr.Assay(frame, id=gene, replicates=1)
    assay.efficiency(factor / 2)
    processed.append(analyser.pipe(assay))
result = qpcr.Normaliser().pipe([processed[0]], [processed[1]], mode="pair-wise")
print(result.get().to_string(index=False))
