import os
import joblib
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier

# Label convention:
# 1 = malicious/suspicious
# 0 = benign/normal
malicious_samples = [
    "admin' or '1'='1",
    "' or 'a'='a",
    "drop table users",
    "<script>alert(1)</script>",
    "union select",
    "-- comment",
    "/* comment */",
    "xp_cmdshell",
    "select * from users",
    "insert into",
    "update users set",
]

benign_samples = [
    "hello world",
    "admin",
    "password123",
    "john",
    "maria",
    "letmein123",
    "contact us",
    "mlUser",
    "mlPass123",
    "nice website",
    "search query",
    "my name is tasrif",
]

X_text = malicious_samples + benign_samples
y = [1] * len(malicious_samples) + [0] * len(benign_samples)

# HashingVectorizer supports streaming/incremental learning (no vocab needed)
vectorizer = HashingVectorizer(
    n_features=2**18,
    alternate_sign=False,
    analyzer="char",
    ngram_range=(3, 5)
)

X = vectorizer.transform(X_text)

# SGDClassifier supports partial_fit => adaptive learning
clf = SGDClassifier(loss="log_loss", random_state=42)
clf.partial_fit(X, y, classes=[0, 1])

os.makedirs("ml_models", exist_ok=True)
joblib.dump({"vectorizer": vectorizer, "model": clf}, "ml_models/ml_defense.joblib")

print("✅ Saved: ml_models/ml_defense.joblib")