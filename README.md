# ai-dj

# **Intelligent DJ Web Application**

### **AI-Powered DJ Web Application for Real-Time Song Requests and Automatic Audio Mixing**

## **Overview**

This project was developed as my final **Computer Science Academy capstone project**. Inspired by my interest in music and building playlists for parties, I wanted to explore whether a web application could recreate some of the decision-making involved in a live DJ set.

The application allows **guests to connect from their phones and submit song requests**, while the DJ system manages those requests and automatically creates transitions between locally stored MP3 tracks.

To create smoother, DJ-style transitions, the application analyzes audio characteristics such as **energy peaks and musical compatibility** before determining where one song should transition into the next.

The project combines **real-time networking, web development, audio analysis, and automated music mixing** into one application.

## **Key Features**

* 📱 **Phone-Based Song Requests** — Guests can connect to the application from their phones and submit songs.
* 🎵 **Real-Time Request Management** — Song requests are communicated between connected devices using WebSockets.
* 🎧 **Automatic Music Mixing** — The application analyzes tracks and determines transition points automatically.
* 📊 **Audio Analysis** — Essentia is used to analyze audio characteristics and identify energy peaks.
* 🔀 **Harmonic Mixing** — Musical compatibility is considered when determining how tracks should transition.
* 🎚️ **Crossfade-Style Transitions** — Songs are blended together instead of simply ending and starting.
* 💻 **Web-Based Interface** — The frontend was built using HTML, CSS, and JavaScript.
* 🎶 **Local Audio Playback** — The application works with locally stored MP3 files.

## **How It Works**

The application follows a multi-step process to turn guest requests into a continuous DJ-style mix.

### **1. Guest Connects**

Guests access the web application from their phones and connect to the DJ system.

### **2. Song Request**

A guest submits a song request through the web interface.

The request is sent to the backend using **WebSockets**, allowing the system to communicate with connected devices in real time.

### **3. Request Management**

The backend receives and manages incoming song requests before determining which track should be played next.

### **4. Audio Analysis**

Before creating a transition, the system analyzes the audio using **Essentia** and other audio-processing libraries.

The analysis is used to identify characteristics such as:

* Energy levels
* Energy peaks
* Musical compatibility
* Appropriate transition points

### **5. Transition Selection**

The system uses the analyzed audio information and **harmonic mixing principles** to determine a suitable point for transitioning between songs.

Rather than simply crossfading at an arbitrary time, the application attempts to transition when the music is better suited for a blend.

### **6. Automatic Mix**

The selected tracks are blended using a **crossfade-style transition**, creating a more continuous listening experience similar to a live DJ set.

## **Technology**

This project was developed using:

| **Technology**      | **Purpose**                                     |
| ------------------- | ----------------------------------------------- |
| **Python**          | Backend logic and audio-processing pipeline     |
| **WebSockets**      | Real-time communication between devices         |
| **HTML**            | Web application structure                       |
| **CSS**             | User interface styling                          |
| **JavaScript**      | Frontend functionality and user interaction     |
| **Essentia**        | Audio analysis and music information extraction |
| **Librosa**         | Audio processing and analysis                   |
| **NumPy**           | Numerical operations used in audio processing   |
| **Anaconda Prompt** | Python environment configuration                |
| **Linux WSL**       | Linux-based audio-processing environment        |

## **Audio Analysis & Mixing**

One of the main challenges of this project was creating transitions that felt intentional rather than simply connecting two songs with a basic crossfade at the end.

### **Energy Analysis**

The application uses **Essentia** to analyze the structure and energy of songs.

By identifying energy peaks, the system can locate parts of a track that may be more appropriate for transitioning into another song.

### **Harmonic Mixing**

The application also considers **harmonic compatibility** when transitioning between songs.

Matching compatible musical keys can help create transitions that sound more natural and cohesive.

### **Crossfade Transitions**

Once a transition point has been selected, the application blends the outgoing and incoming songs instead of using a simple hard cut.

This allows one track to gradually transition into the next.

## **Technical Challenges**

This project required combining several areas of computer science that I had not previously used together in one application.

Some of the biggest challenges included:

### **Real-Time Networking**

The application needed to support communication between multiple phones and the DJ system simultaneously. WebSockets allowed song requests and application events to be communicated in real time.

### **Audio Processing**

Audio analysis required working with specialized libraries such as **Essentia** and **Librosa**, as well as understanding how audio data could be processed computationally.

### **Multi-Environment Development**

Some of the audio-processing tools required a Linux-based environment, which led me to configure **Linux through WSL** alongside my Windows development environment.

This required managing different development environments and ensuring that the web application and audio-processing components could work together.

## **Development Process**

The project was developed independently as a final capstone project for my Computer Science Academy.

I designed and implemented the application by combining concepts from:

* Web development
* Backend programming
* Real-time communication
* Audio analysis
* Data processing
* Algorithmic music mixing

The project gave me an opportunity to take my interest in music and turn it into a larger software engineering problem involving multiple interconnected systems.

## **Project Structure**

The repository is organized around the application's frontend, backend, and audio-processing components.

```text
ai-dj/

│
├── backend/
│   ├── main.py
│   └── ...
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── ...
│
├── automix_engine.py
│
├── ...
│
└── README.md
```

### **File Descriptions**

| **File / Directory** | **Description**                                          |
| -------------------- | -------------------------------------------------------- |
| `backend/`           | Contains backend and real-time communication logic       |
| `frontend/`          | Contains the web application's HTML, CSS, and JavaScript |
| `main.py`            | Main backend application logic                           |
| `automix_engine.py`  | Audio analysis and automatic mixing functionality        |
| `README.md`          | Project documentation                                    |

## **Future Applications**

This project could be expanded into a more complete automated DJ platform.

Potential future directions include:

* Supporting larger music libraries
* Improving automatic transition selection
* Adding beat matching and BPM-based synchronization
* Expanding the audio analysis pipeline
* Adding a more advanced DJ control interface
* Supporting playlists and event-specific queues
* Developing additional mobile-friendly features
* Exploring more sophisticated music recommendation and mixing algorithms

## **What I Learned**

This project taught me how to combine multiple areas of computer science into one working application.

In particular, I gained experience with **WebSockets and real-time networking, full-stack web development, audio data processing, Linux development environments, and algorithmic approaches to music mixing**.

Most importantly, the project showed me how software can connect seemingly different interests. What started as an idea based on building playlists for parties became a technical challenge involving networking, data, audio, and user interaction.

## **Author**

**Aditi Chaugule**

Computer Science Academy Capstone Project
May 2026 – June 2026

This project represents an independent exploration of **web development, real-time systems, audio analysis, and automated music mixing** inspired by my interest in music.

---

### **Disclaimer**

This project is an educational capstone project and is intended for experimentation and learning purposes. It is not intended to replace professional DJ software or equipment.
