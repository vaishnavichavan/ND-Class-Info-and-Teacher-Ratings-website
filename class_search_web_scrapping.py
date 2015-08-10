import requests
from bs4 import BeautifulSoup

def CleanUpString(string):
    """Cleans up a string by getting rid of '\\t', '\\r', '\\n', and double spaces (i.e. '  ').
    Input: string
    Returns: String
    """
    return string.replace('\t', '').replace('\r','').replace('\n', '').replace('  ', '')
    
    
    
def GetOptions():
    """Gets the options for the 6 categories (Term, Division, Campus, Subject, Attribute, and Credits)..
    Gets both the option that is displayed on class-search.nd.edu as well as the option_key that is neccessary 
    to submit the post request in order to navigate to the correct page
    Returns: dictionary of option_descriptions (what is displayed on class-search.nd.edu)
        that point to option_keys{option_description: option_key}
    """
    
    #
    url = 'https://class-search.nd.edu/reg/srch/ClassSearchServlet'
    response = requests.get(url)
    soup = BeautifulSoup(response.content)
    data = soup.find_all('select')
    
    # Dictionaries used to store both option description and the form data value required for post requests
    TermOptions = {}
    DivisionOptions = {}
    CampusOptions  = {}
    SubjectOptions = {}
    AttributeOptions= {}
    CreditsOptions = {}
    
    OptionCategories = [TermOptions, DivisionOptions, CampusOptions, SubjectOptions, AttributeOptions, CreditsOptions]
    
    for i, category in zip(data, OptionCategories):
        options = i.find_all('option')
        for option in options:
            category[CleanUpString(str(option.text))] = str(option).split('"')[1]
        
    return OptionCategories
        



    

def GetClasses(term, subj, credit, Attr, divs, campus):
    """
    Given the inputs, function will find the class data from class-search.nd.edu.
    Inputs: Academic term, Academic subject, number of credits, Attribute type, Academic division, and finally campus. 
       All should be in the form of strings
    Returns: A list of dictionaries, with each dictionary being a specific class at Notre Dame
       Each dictionary has the same keys and gives the same information for each class 
    """
    url = 'https://class-search.nd.edu/reg/srch/ClassSearchServlet'
   
    #divs = 'A'
    #campus = 'M'
    #Attr = '0ANY'
    #credit = 'A'
    
    # stores data for the post request
    FormData = {'TERM': term, 'SUBJ': subj, 'CREDIT':credit, 'ATTR':Attr, 'DIVS':divs, 'CAMPUS' : campus}
    
    response = requests.post(url, data = FormData)
    soup = BeautifulSoup(response.content)
    
    ClassTable = soup.find_all('table', {'id':'resulttable'})[0].find_all('tr')
    
    Headers = ClassTable[0].find_all('th')
    
    # Class_Headers stores the column headers for the class data
    Class_Headers = []
    for header in Headers:
        Class_Headers.append(str(header.text))
    
    
    Classes = ClassTable[1:]
    
    Classlist = []
    
    # Temporary counting variable
    Num_Classes = 0
    URLS = []
    for Class in Classes:
        Classlist.append({})
        Info = Class.find_all('td')
        URLS.append([])
        for i, head in zip(Info,Class_Headers):
            url = ''
            url = i.find_all('a')
            if url:
                URLS[Num_Classes].append(url)
            Classlist[Num_Classes][head] = CleanUpString(str(i.text).replace('\t', ''))
        Num_Classes += 1
    
    
    # Reassign temporary counting variable
    Num_Classes = 0
    for url in URLS:
        ClassUrlData = url[0]
        ClassDescriptionUrl = ClassUrlData[0].get('href')
        BookStoreUrlData = ClassUrlData[1]
        BookStoreUrl = BookStoreUrlData.get('href')
        ClassUrlExtension = CleanUpString(ClassDescriptionUrl.split("'")[1])
        
        Classlist[Num_Classes]['Course_Info'] = 'https://class-search.nd.edu/reg/srch/' + ClassUrlExtension
        Classlist[Num_Classes]['View_Books'] =  BookStoreUrl
        
        # Some classes have no teacher yet announced. If they do not have a teacher, then len(url) == 1. 
        # If the teacher is announced, len(url) == 2
        if len(url) == 2:
            InstructorUrlData = url[1][0].get('href')
            TeacherUrlExtension = CleanUpString(InstructorUrlData.split("'")[1])
            Classlist[Num_Classes]['Teacher_Info'] = 'https://class-search.nd.edu/reg/srch/' + TeacherUrlExtension
        else:
            Classlist[Num_Classes]['Teacher_Info'] = 'NONE'
        Num_Classes += 1
    
    # Clean up Course - sec in Classlist
    for i in Classlist:
        i['Course - Sec'] = i['Course - Sec'].replace('*View Books', '')

    return Classlist



def GetClassDescriptionAndAll(url):
    """Gets the class description, the course prerequisites, and the course corequisites
    Input: a url of a class specific page
    returns: A list with the course description, a string that reveals the contents of the rest of the list, 
            the prerequisites (if any), and corequisites (if any)
            String options: 'Both', 'Neither', 'Prerequisote Only', or 'Corequisite Only'
    """
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content)
    
    
    DataText = soup.find_all('td')[2].text.split('Restrictions:')[0]
    
    # Now want to get only course description, Prerequisites, and Corequisite 
    Course_Description = DataText.split('Associated Term:')[0]
    
    
    if 'Prerequisites' in DataText:
        if 'Corequisites' in DataText:
            Temporary = DataText.split('Prerequisites:')[1].split('Corequisites:')
            Prerequisites = CleanUpString(str(Temporary[0]))
            Corequisites = CleanUpString(str(Temporary[1]))
            return [Course_Description, 'Both', Prerequisites, Corequisites]
        else:
            Prerequisites = CleanUpString(DataText.split('Prerequisites:')[1])
            return [Course_Description, 'Prerequisite Only', Prerequisites]
    elif 'Corequisites' in DataText:
            Corequisites = CleanUpString(DataText.split('Corequisites:')[1])
            return [Course_Description, 'Corequisite Only', Corequisites]
    else:
        return [Course_Description, 'Neither']


  