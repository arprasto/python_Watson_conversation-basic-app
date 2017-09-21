# -*- coding: utf-8 -*-
import json
from watson_developer_cloud import ConversationV1
import ibm_db
import re


# BEGIN of python-dotenv section
from os.path import join, dirname
from dotenv import load_dotenv
import os, sys
# END of python-dotenv section

def parse_conversation_response(json_data):
    """Parse the response from Conversation and act accordingly.

    Parameters
    ----------
    json_data : {dict} json response from Conversation.

    Returns
    -------
    {dict} : containing the main elements parsed from the response
           ("text", "action", "entities", "intents"...)

    Notes
    -----
    For an example of the JSON structure, see file 'pytest_data/conversation_hello.json'
    """
    #print("parse_conversation_response() not implemented.")
    #out_dict = json_data
    #print(json_data)
    return_dict = {}
    resp_text = ""
    resp_text_count = 0
    output = json_data.get('output')
    texts = output.get('text')
    for text in texts:
        if resp_text_count == 0:
            resp_text = text
            resp_text_count = resp_text_count + 1
        else:
            resp_text = resp_text + "\n" + text
    return_dict['text'] = resp_text
    return return_dict


def handle_conversation_data(parsed_data,input_content,DB_DSN):
    """Handles whatever there needs to be done with the data
    obtained from conversation.
    For instance: prints the answer in a nice format?

    Parameters
    ----------
    parsed_data : {dict} containing the main elements parsed from the response
                   ("text", "action", "entities", "intents"...)

    Returns
    -------
    None
    """
    data_str = ''
    if "member_name" in parsed_data.get('text'):
        print('connecting member_name to DB')
        db_conn = ibm_db.connect(DB_DSN,"","")
        barcode_name_stmt = ibm_db.prepare(db_conn,"SELECT * FROM NAOSCHEMA.BAR_CUSTMAP where BARCODE=?")
        qry_pram = input_content,
        flag = ibm_db.execute(barcode_name_stmt,qry_pram)
        if flag:
            ibm_db.bind_param(barcode_name_stmt,1,input_content)
            dbrow_dictionary = ibm_db.fetch_both(barcode_name_stmt)
            cust_name = ""
            if dbrow_dictionary == False:
                cust_name = "Dear Customer"
            else:
                cust_name = dbrow_dictionary["NAME"]
            data_str = parsed_data.get('text').replace("member_name",cust_name)
            del barcode_name_stmt
            ibm_db.close(db_conn)
            return data_str
        else:
            del barcode_name_stmt
            ibm_db.close(db_conn)
            data_str = parsed_data.get('text').replace("member_name","Dear Customer")
            return data_str

    if "check_offers" in parsed_data.get('text'):
        offers_str = ""
        print('connecting check_offers to DB')
        db_conn = ibm_db.connect(DB_DSN,"","")
        offer_stmt = ibm_db.prepare(db_conn,"SELECT * FROM NAOSCHEMA.OFFERS")
        flag = ibm_db.execute(offer_stmt)
        if flag:
            dbrow_dictionary = ibm_db.fetch_both(offer_stmt)
            while dbrow_dictionary != False:
                offers_str = offers_str +". "+ dbrow_dictionary["OFFER"]
                dbrow_dictionary = ibm_db.fetch_both(offer_stmt)
            if offers_str.strip() == "":
                offers_str = "I can not see any offer for you. Please check with assistant."
            data_str = parsed_data.get('text').replace("check_offers",offers_str)
            del offer_stmt
            ibm_db.close(db_conn)
            return data_str;
        else:
            data_str = "I can not see any offer for you. Please check with assistant."
            del offer_stmt
            ibm_db.close(db_conn)
            return data_str

    if "_location" in parsed_data.get('text'):
        print('connecting location to DB')
        db_conn = ibm_db.connect(DB_DSN,"","")
        stor_loc_stmt = ibm_db.prepare(db_conn,"SELECT * FROM NAOSCHEMA.STORE_LOCATION where STORCODE=?")
        loc_p = re.compile('[a-z]+_location')
        qry_pram = loc_p.match(parsed_data.get('text').lower().strip()).group(),
        qry_str = loc_p.match(parsed_data.get('text').lower().strip()).group()
        print(qry_str)
        flag = ibm_db.execute(stor_loc_stmt,qry_pram)
        if flag:
            ibm_db.bind_param(stor_loc_stmt,1,input_content)
            dbrow_dictionary = ibm_db.fetch_both(stor_loc_stmt)
            STORE_LOCATION = ""
            if dbrow_dictionary == False:
                STORE_LOCATION = "i can not find your store location. please check with assistant."
            else:
                STORE_LOCATION = dbrow_dictionary["LOCATION"]
            data_str = parsed_data.get('text').replace(qry_str,STORE_LOCATION)
            del stor_loc_stmt
            ibm_db.close(db_conn)
            return data_str
        else:
            del stor_loc_stmt
            ibm_db.close(db_conn)
            data_str = parsed_data.get('text').replace(qry_str,"i can not find your store location. please check with assistant.")
            return data_str

    if "read_news" in parsed_data.get('text'):
        news_str = ""
        print('connecting read_news to DB')
        db_conn = ibm_db.connect(DB_DSN,"","")
        news_stmt = ibm_db.prepare(db_conn,"SELECT * FROM NAOSCHEMA.NEWS")
        flag = ibm_db.execute(news_stmt)
        if flag:
            dbrow_dictionary = ibm_db.fetch_both(news_stmt)
            while dbrow_dictionary != False:
                news_str = news_str +". "+ dbrow_dictionary["highlight"]
                dbrow_dictionary = ibm_db.fetch_both(news_stmt)
            if news_str.strip() == "":
                news_str = "we have very good offers for today."
            data_str = parsed_data.get('text').replace("read_news",news_str)
            del news_stmt
            ibm_db.close(db_conn)
            return data_str;
        else:
            data_str = "we have very good offers for today."
            del news_stmt
            ibm_db.close(db_conn)
            return data_str


    else:
        data_str = parsed_data.get('text')
        return data_str



def main_loop(conversation, workspace_id,DB_DSN):
    """Loops the dialog by asking for a prompt,
    submitting to Watson Conversation, parsing and handling the response.

    Parameters
    ----------
    conversation : {ConversationV1} the connector to Conversation (Watson API).
    workspace_id : {str} id to workspace in Conversation instance.

    Returns
    -------
    None
    """
    # just for debugging
    print('*** Connecting to your workspace...')

    # connects to conversation to start dialog, retrieves the json respose.
    response = conversation.message(message_input=None,
                                    workspace_id=workspace_id)

    # sends the response to our functions
    data = parse_conversation_response(response)
    handle_conversation_data(data,"",DB_DSN)

    # prompt at the beginning of the conversation
    print('(say anything... type quit to quit)')

    # let's do an infinite loop
    while True:
        # gets some input from the prompt
        if sys.version_info[0] < 3:
            input_content = raw_input('You> ')
        else:
            input_content = input('You> ')

        # if you type one of those words, it will exit the while loop
        if (input_content.lower() in {'exit', 'quit', 'q', 'n'}):
            break

        # sends the input to conversation and retrieves the json response.
        response = conversation.message(workspace_id=workspace_id,
                                        message_input={'text': input_content},
                                        context=response.get('context'))

        # sends the response to our functions
        data = parse_conversation_response(response)
        print(handle_conversation_data(data,input_content,DB_DSN))

def start_conversation_thread(CONVERSATION_USERNAME,CONVERSATION_PASSWORD,CONVERSATION_WORKSPACE_ID,DB_DSN):
    # create an instance of the API ConversationV1 object
    conversation_apiobj = ConversationV1(
        username=CONVERSATION_USERNAME,
        password=CONVERSATION_PASSWORD,
        version='2016-09-20')

    # obtain the workspace id from dotenv
    workspace_id_env = CONVERSATION_WORKSPACE_ID
    main_loop(conversation_apiobj, workspace_id_env,DB_DSN)


if __name__ == '__main__':
    # BEGIN of python-dotenv section
    dotenv_path = join(dirname(__file__), '.env')
    if (not os.path.isfile(dotenv_path)):
        sys.stderr.write("ERROR: you are trying to run this script locally,"\
                         " you need to set your credentials in file {}\n".format(dotenv_path))
        sys.exit(1)
    else:
        load_dotenv(dotenv_path)
    # END of python-dotenv section

    start_conversation_thread(os.environ.get("CONVERSATION_USERNAME"),os.environ.get("CONVERSATION_PASSWORD"),os.environ.get("CONVERSATION_WORKSPACE_ID"),os.environ.get("DB_DSN"))
