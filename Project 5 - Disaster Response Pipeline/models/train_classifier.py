import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import warnings
# import NLP libraries
warnings.filterwarnings("ignore")
import re
import nltk 
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer

# import sklearn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier

def load_data(database_filepath):
    # load data from database
    engine = create_engine('sqlite:///Messages.db')
    df = pd.read_sql_table('Messages', engine)
    X = df['message']
    Y = df.drop(['id', 'message', 'original', 'genre'], axis=1)
    category_names = Y.columns
    
    return X, Y, category_names

def tokenize(text):
    # Define url pattern
    url_re = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # Detect and replace urls
    detected_urls = re.findall(url_re, text)
    for url in detected_urls:
        text = text.replace(url, "urlplaceholder")
    
    # tokenize sentences
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    
    # save cleaned tokens
    clean_tokens = [lemmatizer.lemmatize(tok).lower().strip() for tok in tokens]
    
    return clean_tokens


def build_model():    
    # build NLP pipeline - count words, tf-idf, multiple output classifier
    pipeline = Pipeline([
        ('vec', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(RandomForestClassifier()))
    ])
    
    # grid search
    parameters = {'clf__estimator__max_features':['sqrt', 0.5],
              'clf__estimator__n_estimators':[50, 100]}

    cv = GridSearchCV(estimator=pipeline, param_grid = parameters, cv = 5, n_jobs = 10)
   
    return cv


def evaluate_model(model, X_test, Y_test, category_names):
    # predict on the X_test
    y_pred = model.predict(X_test)
    
    # build classification report on every column
    performances = []
    for i in range(len(category_names)):
        performances.append([f1_score(y_test.iloc[:, i].values, y_pred[:, i], average='micro'),
                             precision_score(y_test.iloc[:, i].values, y_pred[:, i], average='micro'),
                             recall_score(y_test.iloc[:, i].values, y_pred[:, i], average='micro')])
    # build dataframe
    performances = pd.DataFrame(performances, columns=['f1 score', 'precision', 'recall'],
                                index = category_names)   
    return performances


def save_model(model, model_filepath):
    pickle.dump(pipeline_improved, open(model_filepath, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()