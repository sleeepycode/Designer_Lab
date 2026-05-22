
# ML Metrics and Evaluation

## Components

1. Report structure analysis
2. OCR
3. Image classification
4. Caption generation
5. Placement logic
6. JSON contract validation

---

# Metrics

## 1. Section Detection Accuracy

Formula:

Accuracy = correctly_found_sections / expected_sections

Example:

Expected:
- introduction
- theory
- practice
- conclusion
- references

Found:
- introduction
- practice
- conclusion

Accuracy = 3 / 5 = 0.60

---

## 2. Missing Sections Precision / Recall

Precision:
correct_missing_found / all_found_missing

Recall:
correct_missing_found / all_real_missing

---

## 3. Image Classification Accuracy

Accuracy = correctly_classified_images / total_images

Example:

8 / 10 = 0.8

---

## 4. OCR Keyword Match

keyword_score = found_keywords / expected_keywords

Example:

Expected:
- график
- температура
- время

Found:
- график
- температура

Score = 2 / 3 = 0.67

---

## 5. Placement Logic Accuracy

Accuracy = correct_placements / total_images

---

## 6. Caption Validation

Checks:
- caption is not empty
- contains image type
- contains keywords
- matches format

---

# Evaluation Pipeline

1. Load report
2. Run analyze_project()
3. Compare result with expected.json
4. Calculate metrics
5. Save metrics_report.json

