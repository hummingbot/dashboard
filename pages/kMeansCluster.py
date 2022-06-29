import streamlit as st
import pandas as pd
import base64
import numpy as np
import plotly.graph_objects as go

from lightgbm import LGBMClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import cross_val_score
import shap


@st.cache(allow_output_mutation=True)
def profile_clusters(df_profile, categorical=None):
    # get the important features via LGBM and SHAP
    X = df_profile.drop('cluster', axis=1)
    y = df_profile['cluster']

    clf = LGBMClassifier(class_weight='balanced', colsample_bytree=0.6)
    scores = cross_val_score(clf, X, y, scoring='f1_weighted')

    print(scores.mean())
    # Fit the model if
    if scores.mean() > 0.5:
        clf.fit(X, y)
    else:
        raise ValueError("Clusters are not distinguishable. Can't profile. ")

    # Get importance
    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X)

    # Get 7 most important features
    importance_dict = {f: 0 for f in X.columns}
    topn = 7
    topn = min(len(X.columns), topn)
    for c in np.unique(df_profile['cluster']):
        shap_df = pd.DataFrame(shap_values[c], columns=X.columns)
        abs_importance = np.abs(shap_df).sum()
        for f in X.columns:
            importance_dict[f] += abs_importance[f]

    importance_dict = {k: v for k, v in sorted(importance_dict.items(), key=lambda item: item[1], reverse=True)}
    important_features = [k for k, v in importance_dict.items()]
    n_important_features = [k for k, v in importance_dict.items()][:topn]

    # Dataframe output
    for k in np.unique(df_profile['cluster']):
        if k == 0:
            profile = pd.DataFrame(columns=['cluster', 'feature', 'mean_value'], index=range(len(n_important_features)))
            profile['cluster'] = k
            profile['feature'] = n_important_features
            profile['mean_value'] = df_profile.loc[df_profile.cluster == k, n_important_features].mean().values
        else:
            profile_2 = pd.DataFrame(columns=['cluster', 'feature', 'mean_value'],
                                     index=range(len(n_important_features)))
            profile_2['cluster'] = k
            profile_2['feature'] = n_important_features
            profile_2['mean_value'] = df_profile.loc[df_profile.cluster == k, n_important_features].mean().values
            profile = pd.concat([profile, profile_2])

    profile.reset_index(drop=True, inplace=True)

    # Scaling for plotting
    for c in X.columns:
        df_profile[c] = MinMaxScaler().fit_transform(np.array(df_profile[c]).reshape(-1, 1))

    # Plotly output
    cluster_names = [f'Cluster {k}' for k in np.unique(df_profile['cluster'])]  # clust 1, 2, 3
    data = [go.Bar(name=f, x=cluster_names, y=df_profile.groupby('cluster')[f].mean()) for f in n_important_features]
    fig = go.Figure(data=data)
    # Change the bar mode
    fig.update_layout(barmode='group')

    return fig, profile, important_features

def profile_feature(df_profile, feature):
    if df_profile[feature].nunique() > 2:
        box_data = [go.Box(y=df_profile.loc[df_profile.cluster == k, feature].values, name=f'Cluster {k}') for k in np.unique(df_profile.cluster)]
        fig = go.Figure(data=box_data)
    else:
        x =[f'Cluster {k}' for k in np.unique(df_profile.cluster)]
        y = [df_profile.loc[df_profile.cluster == k, feature].mean() for k in np.unique(df_profile.cluster)]
        fig = go.Figure([go.Bar(x=x, y=y)])
    return fig

def get_table_download_link(df, filename, linkname):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{linkname}</a>'
    return href

prof = False
st.title('AutoCluster - By Souvik Roy ©The_Divine_Academy/Souvik_Roy')
st.sidebar.markdown('## Data Import')
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.markdown('### Data Sample')
    st.write(data.head())
    id_col = st.sidebar.selectbox('Pick your ID column', options=data.columns)
    cat_features = st.sidebar.multiselect('Pick your categorical features', options=[c for c in data.columns], default = [v for v in data.select_dtypes(exclude=[int, float]).columns.values if v != id_col])
    clusters = data['cluster']
    df_p = data.drop(id_col, axis=1)
    if cat_features:
        df_p = pd.get_dummies(df_p, columns=cat_features) #OHE the categorical features
    prof = st.checkbox('Check to profile the clusters')

else:
    st.markdown("""
    <br>
    <br>
    <br>
    <br>
    <br>
    <br>
    <h1 style="color:#26608e;"> Upload your CSV file to begin clustering </h1>
    <h3 style="color:#f68b28;"> Project from course - Data Science for Marketing By ©The_Divine_Academy </h3>
    """, unsafe_allow_html=True) 

if (prof == True) & (uploaded_file is not None):
    fig, profiles, imp_feat = profile_clusters(df_p, categorical=cat_features)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown(f'<h3 "> Profiles for {len(np.unique(clusters))} Clusters </h3>',
                            unsafe_allow_html=True)
    fig.update_layout(
        autosize=True,
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=40,
                pad=0
            ),
        )
    st.plotly_chart(fig)

    show = st.checkbox('Show up to 20 most important features')
    if show == True:
        l = np.min([20, len(imp_feat)])
        st.write(imp_feat[:l])

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown(f'<h3 "> Features Overview </h3>',
                unsafe_allow_html=True)
    feature = st.selectbox('Select a feature...', options = df_p.columns)
    feat_fig = profile_feature(df_p, feature)
    st.plotly_chart(feat_fig)

    st.subheader('Downloads')
    st.write(get_table_download_link(profiles,'profiles.csv', 'Download profiles'), unsafe_allow_html=True)

elif (prof == False) & (uploaded_file is not None):
    st.markdown("""
    <br>
    <h2 style="color:#26608e;"> Data is read in. Check the box to profile </h2>
    """, unsafe_allow_html=True) 

