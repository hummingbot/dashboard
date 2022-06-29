import pandas as pd
#import pickle
import streamlit as st 
import base64

#@st.cache
def main():
  try:
   
    #st.title("Personal Loan Authenticator")
    html_temp = """
    <div style="background-color:tomato;padding:10px">
    <h2 style="color:white;text-align:center;">Souvik Roy's Auto ML App ©Souvik1406 </h2>
    </div>
    """
    st.markdown(html_temp,unsafe_allow_html=True)
    from PIL import Image
    image_loan=Image.open("ml4.jpg")
    st.sidebar.title("Upload Input csv file : ")
    file_upload=st.sidebar.file_uploader(" ",type=["csv"])
    st.sidebar.image(image_loan,use_column_width=True) 

    
    if file_upload is not None:
            f1=pd.read_csv(file_upload)
            f1.isna().sum()
            f1=f1.dropna()
            X=f1[['age','previous_year_rating','length_of_service','KPI_Met','awards_won']]
            y=f1['is_promoted']
            d2=f1[['age','previous_year_rating','length_of_service','KPI_Met','awards_won','is_promoted']]
            st.text(" ")
            if st.checkbox('Show Input Data'):
                st.write(d2)
            st.subheader("Pick Your Algorithm") 
            choose_model=st.selectbox(label=' ',options=[' ','Random Forest','Logistic Regression'])
            if (choose_model=='Random Forest'):
                from sklearn.model_selection import train_test_split
                X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.3,random_state=0)
                from sklearn.ensemble import RandomForestClassifier
                classifier=RandomForestClassifier()
                classifier.fit(X_train, y_train)
                y_pred=classifier.predict(X_test)
                from sklearn.metrics import accuracy_score
                score=accuracy_score(y_test,y_pred)
                from sklearn.metrics import confusion_matrix
                c1=confusion_matrix(y_test,y_pred)
                st.write("Model Accuracy : ", score)
                st.write("Confusion Matrix : ", c1)
                from sklearn.model_selection import cross_val_score
                cv=cross_val_score(classifier,X_train, y_train,cv=5,scoring='accuracy')
                st.write("Cross Calidation of Model : ", cv)
                import matplotlib.pyplot as plt
                from sklearn import metrics
                y_pred_proba = classifier.predict_proba(X_test)[::,1]
                fpr, tpr, _ = metrics.roc_curve(y_test,  y_pred_proba)
                auc = metrics.roc_auc_score(y_test, y_pred_proba)
                plt.plot(fpr,tpr,label="data 1, auc="+str(auc))
                plt.legend(loc=4)
                st.subheader("ROC Curve")
                st.pyplot(plt)
                st.subheader("Upload csv file for Predictions : ")
                file_upload=st.file_uploader("  ",type=["csv"])
                if file_upload is not None:
                    data=pd.read_csv(file_upload)
                    data1=data.dropna()
                    data=data1[['age','previous_year_rating','length_of_service','KPI_Met','awards_won']]
                    predictions=classifier.predict(data)
                    data['employee_id'] = data1['employee_id']
                    data['Prediction'] = predictions
                    st.subheader("Find the Predicted Results below :")
                    st.write(data)
                    st.text("0 : Not Eligible for Promotion")
                    st.text("1 : Eligible for Promotion")
                    csv = data.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
                    href = f'<a href="data:file/csv;base64,{b64}">Download The Prediction Results CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
                    st.markdown(href, unsafe_allow_html=True)
                    display_df = st.checkbox(label='Visualize the Predicted Value')
                    if display_df:
                        st.bar_chart(data['Prediction'].value_counts())
                        st.text(data['Prediction'].value_counts())  
            if (choose_model=='Logistic Regression'):
                from sklearn.model_selection import train_test_split
                X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.3,random_state=0)
                from sklearn.linear_model import LogisticRegression
                classifier = LogisticRegression()
                classifier.fit(X_train, y_train)
                y_pred=classifier.predict(X_test)
                from sklearn.metrics import accuracy_score
                score=accuracy_score(y_test,y_pred)
                from sklearn.metrics import confusion_matrix
                c1=confusion_matrix(y_test,y_pred)
                st.write("Model Accuracy : ", score)
                st.write("Confusion Matrix : ", c1)
                
                from sklearn.model_selection import cross_val_score
                cv=cross_val_score(classifier,X_train, y_train,cv=5,scoring='accuracy')
                st.write("Cross Calidation of Model : ", cv)
                import matplotlib.pyplot as plt
                from sklearn import metrics
                y_pred_proba = classifier.predict_proba(X_test)[::,1]
                fpr, tpr, _ = metrics.roc_curve(y_test,  y_pred_proba)
                auc = metrics.roc_auc_score(y_test, y_pred_proba)
                plt.plot(fpr,tpr,label="data 1, auc="+str(auc))
                plt.legend(loc=4)
                st.subheader("ROC Curve")
                st.pyplot(plt)
                st.subheader("Upload csv file for Predictions : ")
                file_upload=st.file_uploader("  ",type=["csv"])                             
                if file_upload is not None:
                    data=pd.read_csv(file_upload)
                    data1=data.dropna()
                    data=data1[['age','previous_year_rating','length_of_service','KPI_Met','awards_won']]
                    predictions=classifier.predict(data)
                    data['employee_id'] = data1['employee_id']
                    data['Prediction'] = predictions
                    st.subheader("Find the Predicted Results below :")
                    st.write(data)
                    st.text("0 : Not Eligible for Promotion")
                    st.text("1 : Eligible for Promotion")
                    csv = data.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
                    href = f'<a href="data:file/csv;base64,{b64}">Download The Prediction Results CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
                    st.markdown(href, unsafe_allow_html=True)
                    display_df = st.checkbox(label='Visualize the Predicted Value')
                    if display_df:
                        st.bar_chart(data['Prediction'].value_counts())
                        st.text(data['Prediction'].value_counts())  
                        
  except:
    st.header("An Error occurred")           
                      
if __name__=='__main__':
    main()
