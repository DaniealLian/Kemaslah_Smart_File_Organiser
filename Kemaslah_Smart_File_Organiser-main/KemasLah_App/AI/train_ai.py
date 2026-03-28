import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier # NEW: VotingClassifier added
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import json 

# 1. Load your chosen dataset
print("Loading dataset...")
# Ensure bbc_data.csv is sitting in the same folder as this script
df = pd.read_csv("bbc_data.csv")

# 2. Map raw labels to clean Folder Names for your GUI
category_map = {
    "business": "Business & Finance",
    "tech": "Technology & IT",
    "politics": "Politics & Government",
    "sport": "Sports",
    "entertainment": "Entertainment & Media"
}
df['Folder_Name'] = df['labels'].map(category_map)

# 3. Split into Training (80%) and Testing (20%)
X_train, X_test, y_train, y_test = train_test_split(
    df['data'], df['Folder_Name'], test_size=0.2, random_state=42
)

# 4. TF-IDF: Convert text to numerical features
print("Vectorizing text...")
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# 5. Train Model A: Support Vector Machine (SVM)
print("Training SVM Model...")
svm_model = SVC(kernel='linear', probability=True) # probability=True allows for 'soft' voting if needed later
svm_model.fit(X_train_tfidf, y_train)
svm_predictions = svm_model.predict(X_test_tfidf)

# 6. Train Model B: Random Forest
print("Training Random Forest Model...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train_tfidf, y_train)
rf_predictions = rf_model.predict(X_test_tfidf)

# --- 7. NEW: TRAIN THE ENSEMBLE "SUPER BRAIN" (STEP 1 UPDATE) ---
print("Training Ensemble (Super Brain) Model...")
# This combines the "experts" into one panel of judges
ensemble_model = VotingClassifier(
    estimators=[('svm', svm_model), ('rf', rf_model)],
    voting='hard' # 'hard' uses the majority vote of the two models
)
ensemble_model.fit(X_train_tfidf, y_train)
ensemble_predictions = ensemble_model.predict(X_test_tfidf)

# 8. Save the "Brains" (.pkl files)
print("Saving .pkl files...")
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
joblib.dump(svm_model, 'svm_model.pkl')
joblib.dump(rf_model, 'rf_model.pkl')
joblib.dump(ensemble_model, 'ensemble_model.pkl') # Save the new combined model

# --- 9. DEEP DIVE ANALYSIS (VISUALIZATION) ---
print("\n9. Generating Evaluation Reports...")
print(f"--> SVM Accuracy: {accuracy_score(y_test, svm_predictions) * 100:.2f}%")
print(f"--> Random Forest Accuracy: {accuracy_score(y_test, rf_predictions) * 100:.2f}%")
print(f"--> Ensemble (Super Brain) Accuracy: {accuracy_score(y_test, ensemble_predictions) * 100:.2f}%")

# Create the confusion matrix for the Ensemble model (The most advanced one)
cm = confusion_matrix(y_test, ensemble_predictions)
folder_names = sorted(category_map.values())

# Heatmap Visualization
plt.figure(figsize=(10, 7))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=folder_names, 
            yticklabels=folder_names)
plt.title('Super Brain Confusion Matrix (Ensemble Model)')
plt.ylabel('Actual Category')
plt.xlabel('AI Predicted Category')
plt.tight_layout()
plt.show()

# --- 10. SAVE METRICS FOR THE UI ---
print("\n10. Saving metrics for the Statistics Dashboard...")

# We use the Ensemble results for the Statistics tab to show the "Best" performance
report_dict = classification_report(y_test, ensemble_predictions, output_dict=True)

# Save to a JSON file that the Kemaslah App can read
with open('ai_metrics.json', 'w') as f:
    json.dump(report_dict, f, indent=4)

print("Metrics saved to 'ai_metrics.json'!")
print("\nSuccess! Super Brain trained and ready for Kemaslah.")