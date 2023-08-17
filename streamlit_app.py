import os
import glob
import numpy as np
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from snowflake.snowpark.session import Session
import streamlit as st
import pandas as pd

# snowpark connection
CONNECTION_PARAMETERS = {
   "account": st.secrets['account'], 
   "user": st.secrets['user'],
   "password": st.secrets['password'],
   "database": st.secrets['database'],
   "schema": st.secrets['schema'],
   "warehouse": st.secrets['warehouse'], 
}


# create session
session = Session.builder.configs(CONNECTION_PARAMETERS).create()



# attendees = session.read.table("EMP")
# # print(attendees.show())
# st.write(attendees)
 
# Verify the code and mark attendance

 

# Verify the code and mark attendance
# Verify the code and mark attendance
def verify_and_mark_attendance(verification_code):
    attendees = session.read.table("EMP")
    filtered_attendee = attendees.filter(attendees["CODE"] == verification_code).filter(~attendees["ATTENDED"])
    if len(filtered_attendee.collect()) > 0:
        attendee_id = filtered_attendee.collect()[0]["ATTENDEE_ID"]
        
        # Mark attendee as attended using the DataFrame API
        attendees_to_update = attendees.filter(attendees["CODE"] == verification_code).filter(~attendees["ATTENDED"])
        attendees_to_update = attendees_to_update.transform(lambda row: row.withColumn("ATTENDED", True))
        
        # Create a new DataFrame containing the updated rows
        updated_attendees = attendees_to_update.select("ATTENDEE_ID", "ATTENDED")
        
        # Update the original attendee table by joining with the updated rows
        attendees = attendees.join(updated_attendees, on=["ATTENDEE_ID"], how="left")
        attendees = attendees.drop("ATTENDED_x").withColumnRenamed("ATTENDED_y", "ATTENDED")
        
        # Update event statistics
        statistics = session.read.table("EVENT_STATISTICS")
        statistics = statistics.filter("EVENT_DATE = CURRENT_DATE()")
        statistics = statistics.withColumn("TOTAL_VERIFIED", statistics["TOTAL_VERIFIED"] + 1)
        statistics = statistics.withColumn("TOTAL_ATTENDED", statistics["TOTAL_ATTENDED"] + 1)
        
        # Update the event statistics table by merging the changes
        session.read.table("EVENT_STATISTICS").merge(statistics, on=["EVENT_DATE"])
        
        return attendee_id
    else:
        return None

# ... (rest of the Streamlit app code)


# Streamlit app
st.title('Event Attendance Verification')
verification_code = st.text_input('Enter Verification Code:')
if st.button('Verify'):
    if verification_code:
        attendee_id = verify_and_mark_attendance(verification_code)
        if attendee_id is not None:
            st.success(f'Code verified successfully for Attendee ID: {attendee_id}! They are marked as attended.')
        else:
            st.error('Invalid code or code already used.')

# Display the attendee table
attendees = session.read.table("EMP")
st.write(attendees)

# Display event statistics
statistics = session.read.table("EVENT_STATISTICS")
st.write(statistics)

