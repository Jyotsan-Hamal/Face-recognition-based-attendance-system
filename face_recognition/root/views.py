import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Student  # replace with your actual Student model
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
import time
from datetime import date
import cv2
import numpy as np
import psycopg2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import io

net = cv2.dnn.readNetFromCaffe('./dnn_model/deploy.prototxt.txt', './dnn_model/res10_300x300_ssd_iter_140000.caffemodel')


def detect_and_crop_faces(image,output_path):
    # Load the model
    
    (h, w) = image.shape[:2]

    # Preprocess the image
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))

    # Pass the blob through the network to detect faces
    net.setInput(blob)
    detections = net.forward()

    # Loop over the detections
    for i in range(0, detections.shape[2]):
        # Extract the confidence (i.e., probability) associated with the prediction
        confidence = detections[0, 0, i, 2]

        # Filter out weak detections by ensuring the `confidence` is greater than a minimum confidence
        if confidence > 0.5:
            # Compute the (x, y)-coordinates of the bounding box for the object
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # Crop the face
            cropped_face = image[startY:endY, startX:endX]

            # Save the cropped face to a new file
            
            cv2.imwrite(output_path, cropped_face)
           

    # Return None if no face is detected
    return None


def landing_page(request):
    if request.method == 'POST':
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:

            login(request, user)
            request.session['username'] = username
            request.session['password'] = password
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'landing_page.html')
        

    else:   
        
        return render(request, 'landing_page.html')

    
@login_required(login_url="landing_page")
def dashboard_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please input username and password")
        return redirect('landing_page')
    else:
        DATABASE_URL = 'postgresql://postgres:2*aA2*eFec-bB3AfF14B-ad4G*gAb*dD@monorail.proxy.rlwy.net:39199/railway'

        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cur = conn.cursor()

            # Fetch the total number of students
            select_query = "SELECT COUNT(*) AS total_students FROM student_table;"
            cur.execute(select_query)
            total_students = cur.fetchone()[0]

            # Close the cursor and connection
            cur.close()
            conn.close()

            # Pass the total_students value to the template
            return render(request, 'dashboard.html', {'total_students': total_students})

        except psycopg2.Error as e:
            # Handle the error appropriately, e.g., log it or show a user-friendly message
            messages.error(request, "Error connecting to the database.")
            return redirect('landing_page')  
    
    
def user_logout(request):
    logout(request)
    request.session.clear()
    messages.error(request, "Logout Succesfully")  
    return redirect("landing_page")

def classroom(request):
    return render(request,"classroom.html")

@login_required
def class_details(request, class_number):
    # Fetch students in the class
    students = Student.objects.filter(class_number=class_number)

    context = {
        'class_number': class_number,
        'students': students,
    }

    return render(request, 'detailstb.html', context)


def image_cropper(image):
    pass

@login_required
def add_student(request,class_number):
    if request.method == 'POST':
        name = request.POST.get('name')
        class_number = request.POST.get('class_number')
        name_parts = name.lower().split(" ")
        first_name = name_parts[0]
        # Access the uploaded image files
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        
        present_day = 1
        today_date = date.today()
        try:
            student = Student.objects.create(
                name=name, 
                class_number=class_number,
                total_present = present_day,
                date=today_date,
                )
            created_sid = student.sid
            
            messages.error(request, "Person added successfully")
            # Save the images in the new directory
            student_dir = os.path.join(f'dataset', f'id{created_sid}')
            os.makedirs(student_dir, exist_ok=True)
            if image1:
                image1_array = cv2.imdecode(np.frombuffer(image1.read(), np.uint8), -1)
                
                output_path = os.path.join(student_dir, f'{first_name}0.jpg')
                detect_and_crop_faces(image1_array,output_path)
            else:
                messages.error(request, "Please add images in image 1")
                return render(request, 'register_student.html', {'class_number': class_number})
            
            if image2:
                image2_array = cv2.imdecode(np.frombuffer(image2.read(), np.uint8), -1)
                
                output_path = os.path.join(student_dir, f'{first_name}1.jpg')
                detect_and_crop_faces(image2_array,output_path)
            else:
                messages.error(request, "Please add images in image 2")
                return render(request, 'register_student.html', {'class_number': class_number})
            
            if image3:
                image3_array = cv2.imdecode(np.frombuffer(image3.read(), np.uint8), -1)
                
                output_path = os.path.join(student_dir, f'{first_name}2.jpg')
                detect_and_crop_faces(image3_array,output_path)
            else:
                messages.error(request, "Please add images in image 3")
                return render(request, 'register_student.html', {'class_number': class_number})

            return redirect(reverse('add_student', kwargs={'class_number': class_number}))
        except:
            
            messages.error(request, "eRROr successfully")
            return redirect(reverse('add_student', kwargs={'class_number': class_number}))

    else:   
        context = {
            'class_number':int(class_number)
        }
        return render(request, 'register_student.html', context)
    
