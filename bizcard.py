import easyocr
import mysql.connector
import pandas as pd
import os
import re
import io
from PIL import Image
import numpy as np
import streamlit as st
from streamlit_option_menu import option_menu

#--------------------------------------------------------------------Image to Text conversion-----------------------------------------------------------------------------------------------------------------#
def txt_img(path):
    user_img=Image.open(path)
    img_array=np.array(user_img)
    Lang=easyocr.Reader(['en'])#en is english
    txt=Lang.readtext(img_array,detail=0)
    return txt,user_img

#---------------------------------------------------------------------Text to Dataframe conversion-------------------------------------------------------------------------------------------------------------#

def txt_retrival(image):
    retrive_txt={'Name':[], 'Designation':[],'Phone':[],'Mail_id':[],'Website':[],'Company_name':[],'Address':[],'State':[],'Pincode':[]}
    for ind,i in enumerate(image):
        #phone No
        if'-'in i:
            retrive_txt['Phone'].append(i)
        elif len(retrive_txt["Phone"]) ==2:
            retrive_txt['Phone'] = " & ".join(retrive_txt['Phone'])
        #Mail ID
        elif '@' in i and (i.lower().endswith('.com')):
            retrive_txt['Mail_id'].append(i)
        #Website
        elif "www " in i.lower() or "www." in i.lower():
            retrive_txt['Website'].append(i)
        elif "WWW" in i:
            retrive_txt["Website"] = image[4] +"."+ image[5]
        # company Name
        elif ind == len(image)-1:
            retrive_txt['Company_name'].append(i)
        #card holder name
        elif ind == 0:
            retrive_txt['Name'].append(i)
        #designation
        elif ind == 1:
            retrive_txt['Designation'].append(i)
        # Address
        if re.findall('^[0-9].+, [a-zA-Z]+',i):
            retrive_txt["Address"].append(i.split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+',i):
            retrive_txt['Address'].append(i)
        match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
        match3 = re.findall('^[E].*',i)

        if match1:
           retrive_txt['Address'].append(match1[0])
        elif match2:
            retrive_txt['Address'].append(match2[0])
        elif match3:
            retrive_txt['Address'].append(match3[0])

        #State
        elif re.findall('[a-zA-Z]{9} +[0-9]',i):
           retrive_txt["State"].append(i[:9])
        elif re.findall('^[0-9].+,([a-zA-Z]+);',i):
            retrive_txt["State"].append(i.split()[-1])
        elif len(retrive_txt["State"])==2:
                    retrive_txt["State"].pop(0)


        #pincode
        if len(i)>=6 and i.isdigit():
            retrive_txt["Pincode"].append(i)
        elif re.findall('[a-zA-Z]{9} +[0-9]',i):
            retrive_txt["Pincode"].append(i[10:])

    for key,value in retrive_txt.items():
        if len(value)>0:
            concad=' '.join(value)
            retrive_txt[key]= [concad]
        else:
            value='NA'
            retrive_txt[key]=[value]

    return retrive_txt
#-----------------------------------------------------------------Streamlit Part--------------------------------------------------------------------------------------------------------------------------------------#
st.set_page_config(page_title='Bizcard Project', layout="wide")

st.title('BizCardX: Extracting Business Card Data with OCR')
with st.sidebar:
    select= option_menu('Main Menu',['Home','Upload','Preview','Modify','Delete'],icons=["house","cloud-upload","list-task","pencil-square"],menu_icon="cast", default_index=0)

if select=='Home':
    col1,col2=st.columns(2)
    with col1:
        st.image(Image.open(r'D:/project/.venv/biz_card_project/OCR.jpg'),width=400)
    with col2:
        st.image(Image.open(r'D:/project/.venv/biz_card_project/OCR-implementation.jpg'),width=400)
    
    
    col3,col4=st.columns(2)
    with col3:
        st.markdown("##### :blue[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
    with col4:
        st.markdown('''##### :blue[**Overview :**] In this streamlit web app you can extract relevant information from it using easyOCR.You can view, modify or delete the extracted data in this app.This app would also allow users to save the extracted information into a database along with the uploaded business card image.The database would be able to store multiple entries, each with its own business card image and extracted information.''') 
#---------------------------------------------------------------------------------DATA Upload--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
elif select=='Upload':
    st.subheader("Upload the business card")

    input=st.file_uploader("Upload the File",type = ["png","jpg","jpeg"])
    if input is not None:
        st.image(input,width=300)
        text_img,input_img=txt_img(input)
        txt_dict=txt_retrival(text_img)
        if txt_dict:
            st.success('Text Extracted Successfully')
        df=pd.DataFrame(txt_dict)

#------------------------------------------------------------------convert image to bytes---------------------------------------------------------------------------------------------------------------------#
        Image_by=io.BytesIO()
        input_img.save(Image_by, format= "PNG")
        img_data = Image_by.getvalue()
        dict={'IMAGE':[img_data]}
        df_1=pd.DataFrame(dict)

        concat_df=pd.concat([df,df_1],axis=1) #axis=0 for row
        st.dataframe(concat_df)
        button_save=st.button('SAVE',use_container_width=True)

        if button_save:
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="business card"
            )
            mycursor=mydb.cursor(buffered=True)

            Create_table='''CREATE TABLE IF NOT EXISTS Bizcardz(Name VARCHAR(255),Designation VARCHAR(255),Phone VARCHAR(255),Email VARCHAR(255),Website TEXT,Company_name VARCHAR(255),
                             Address TEXT,State TEXT,Pincode VARCHAR(255),Image LONGBLOB)'''
            mycursor.execute(Create_table)
            mydb.commit()
            
            insert_q='''INSERT INTO Bizcardz(Name,Designation,Phone,Email,Website,Company_name,Address,State,Pincode,Image)
                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '''
            table_data=concat_df.values.tolist()[0]
            mycursor.execute(insert_q,table_data)
            mydb.commit()
            st.success('Data saved successfully')

#----------------------------------------------------------DATA preview-----------------------------------------------------------------------------------------------#
elif select=='Preview':
    st.subheader("Preview the card information")
     
    mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="business card"
                 )
    mycursor=mydb.cursor(buffered=True)
    mycursor.execute('SELECT * FROM Bizcardz' )
    out=mycursor.fetchall()
    mydb.commit()
    
    out_df=pd.DataFrame(out,columns=('Name','Designation','Phone','Email','Website','Company_name','Address','State','Pincode','Image'))

    st.dataframe(out_df)
#---------------------------------------------------------------DATA Modification-------------------------------------------------------------------------------------------------------------------------#
elif select=='Modify':
    st.subheader("Modification of Data")

    mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="business card"
                 )
    mycursor=mydb.cursor(buffered=True)
    mycursor.execute('SELECT * FROM Bizcardz' )
    out=mycursor.fetchall()
    mydb.commit()
    out_df=pd.DataFrame(out,columns=('Name','Designation','Phone','Email','Website','Company_name','Address','State','Pincode','Image'))

    col1,col2=st.columns(2)
    with col1:
        select_name=st.selectbox('SELECT THE NAME',out_df['Name'])
    df3=out_df[out_df['Name']==select_name]
    df4=df3.copy()
    
    col1,col2=st.columns(2)
    with col1:
        modify_name=st.text_input('NAME',df3['Name'].unique()[0])
        modify_desig = st.text_input('DESIGNATION',df3['Designation'].unique()[0])
        modify_phone = st.text_input("PHONE_NO",df3['Phone'].unique()[0])
        modify_email = st.text_input("EMAIL",df3['Email'].unique()[0])
        modify_website= st.text_input("WEBSITE",df3['Website'].unique()[0])

        df4['Name']=modify_name
        df4['Designation']=modify_desig
        df4['Phone']=modify_phone
        df4['Email']=modify_email
        df4['Website']=modify_website

        modify_com_name=st.text_input('COMPANY_NAME',df3['Company_name'].unique()[0])
        modify_address=st.text_input('ADDRESS',df3['Address'].unique()[0])
        modify_state=st.text_input('STATE',df3['State'].unique()[0])
        modify_pincode=st.text_input('PINCODE',df3['Pincode'].unique()[0])
        modify_image=st.text_input('IMAGE',df3['Image'].unique()[0])

        df4['Company_name']=modify_com_name
        df4['Address']= modify_address
        df4['State']= modify_state
        df4['Pincode']=modify_pincode
        df4['Image']= modify_image

    st.dataframe(df4)

    col1,col2=st.columns(2)
    with col1:
        modify_button=st.button('MODIFY')
    
    if modify_button:
        mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="business card"
                 )
        mycursor=mydb.cursor(buffered=True)
        mycursor.execute(f"DELETE FROM Bizcardz WHERE Name='{select_name}'")
        mydb.commit()

        insert_q='''INSERT INTO Bizcardz(Name,Designation,Phone,Email,Website,Company_name,Address,State,Pincode,Image)
                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '''

        modify_data=df4.values.tolist()[0]
        mycursor.execute(insert_q,modify_data)
        mydb.commit()
        st.success('Data Modified successfully')
#------------------------------------------------------------- DATA Deletion------------------------------------------------------------------------------------------------------------#
elif select=='Delete':
    st.subheader("Delete the card Information")

    mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="business card"
                 )
    mycursor=mydb.cursor(buffered=True)

    col1,col2=st.columns(2)
    with col1:
        mycursor.execute('SELECT Name FROM Bizcardz')
        table_1=mycursor.fetchall()
        mydb.commit()
        Name=[]
        for i in table_1:
            Name.append(i[0])
        Names=st.selectbox("Select the name",Name)
        
    with col2:
        mycursor.execute(f"SELECT Designation FROM Bizcardz WHERE Name='{Names}'")
        table_2=mycursor.fetchall()
        mydb.commit()
        Designation=[]
        for i in table_2:
            Designation.append(i[0])
        Designations=st.selectbox('Select the designation',Designation)

    if Names and Designations:
        col1,col2,col3 = st.columns(3)

        with col1 and col2:
            mycursor.execute(f"SELECT Name,Designation,Phone,Email,Website,Company_name,Address,State,Pincode,Image FROM Bizcardz WHERE Name='{Names}'and Designation='{Designations}'")
            output=mycursor.fetchall()
            mydb.commit()
            output_df=pd.DataFrame(output,columns=('Name','Designation','Phone','Email','Website','Company_name','Address','State','Pincode','Image'))
            st.dataframe(output_df)

        with col1 and col2:
            st.write("")
            Delete = st.button("DELETE",use_container_width=True)

            if Delete:
                mycursor.execute(f"DELETE FROM Bizcardz WHERE Name ='{Names}'and Designation= '{Designations}'")
                mydb.commit()
                st.warning("DATA DELETED SUCCESSFULLY")


