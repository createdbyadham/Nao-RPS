from naoqi import ALProxy
import random
import time
import almath  # For hand angle calculations

# Connect to Nao using the IP address
nao_ip = "10.15.8.61"  # Nao's IP
nao_port = 9559  # Default Naoqi port

# Initialize proxies
tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
tts.setParameter("speed", 80)  # Slow down speech speed 
asr = ALProxy("ALSpeechRecognition", nao_ip, nao_port)
posture = ALProxy("ALRobotPosture", nao_ip, nao_port)
motion = ALProxy("ALMotion", nao_ip, nao_port)
memory = ALProxy("ALMemory", nao_ip, nao_port)
animated_speech = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)

# Define vocabulary for speech recognition
vocabulary = ["rock", "paper", "scissors"]
asr.pause(True)
asr.setVocabulary(vocabulary, False)
asr.pause(False)

def do_rps_motion(hand_name):
    # Nao's hand and arm joint names
    joint_names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]

    # Define angles for the motion (adjust as needed)
    target_angles = [
        [1.5, 0.3, 0.5, 0.0, 0.0, 1.0],    # Arm up, open hand (paper)
        [1.5, 0.3, 0.5, 1.5, 0.0, 0.0],    # Arm up, closed fist (rock)
        [1.5, 0.3, 0.5, 0.0, 0.0, 0.3]     # Arm up, scissors (two fingers open)
    ]

    # Perform the motion three times
    for i in range(3):
        for angles in target_angles:
            motion.angleInterpolationWithSpeed(joint_names, angles, 0.5)
            time.sleep(0.2)

    # Reset hand 
    motion.angleInterpolationWithSpeed(joint_names, target_angles[0], 0.5)

# Function to show Nao's choice with hand gesture
def show_nao_choice(choice, hand_name):
    do_rps_motion(hand_name)
    if choice == "rock":
        target_angles = [1.5, 0.3, 0.5, 1.5, 0.0, 0.0]  # Closed fist (rock)
    elif choice == "paper":
        target_angles = [1.5, 0.3, 0.5, 0.0, 0.0, 1.0]   # Open hand (paper)
    elif choice == "scissors":
        target_angles = [1.5, 0.3, 0.5, 0.0, 0.0, 0.3]  # Scissors (two fingers open)

    joint_names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw", "RHand"]
    motion.angleInterpolationWithSpeed(joint_names, target_angles, 0.5)


# Function to reset Nao to a standing position
def reset_nao():
    posture.goToPosture("Stand", 0.5)
    motion.rest()  # Optional: Relax all joints

def play_rps():
    global rounds_played

    # Greeting and introduction
    tts.say("Hello! I'm Nao, and I'm excited to play Rock-Paper-Scissors with you.")
    time.sleep(2)  # Increased pause for speech clarity
    tts.say("We'll play a couple of rounds. Get ready to challenge me")
    time.sleep(2)  # Increased pause

    nao_wins = 0
    user_wins = 0
    rounds_played = 0

    # Happy and sad expressions for Nao
    happy_expressions = ["(^ ^)", "(≧▽≦)", "\\(^ヮ^)/"]
    sad_expressions = ["(T_T)", "(╥_╥)", "(;-;)"]

    round_intros = [
        "Let's start round {}! Show me what you've got!",
        "Round {} coming up! I hope you're ready!",
        "It's time for round {}. May the best player win!",
        "Round {} is about to begin. Good luck!",
        "Here we go with round {}. Let's see who comes out on top!"
    ]

    # Game loop (play for 5 rounds)
    while rounds_played < 5:
        posture.goToPosture("Stand", 0.5)  # Ensure Nao is standing at the start of each round
        time.sleep(1)  # Pause to allow Nao to fully stand

        tts.say(random.choice(round_intros).format(rounds_played + 1))
        
        # Robot's random choice
        try:
            nao_choice = random.choice(vocabulary[:3])
            show_nao_choice(nao_choice, "LHand")  # Show choice with the left hand
            time.sleep(1)  # Pause after showing Nao's choice
        except Exception as e:
            print("Error showing Nao's choice: {}".format(e))
            tts.say("Oops, I had a little trouble there. Let's try again from the beginning.")
            reset_nao()
            continue

        # Get player's choice through voice recognition, with retry
        valid_choice = False
        failed_attempts = 0
        start_time = time.time()
        user_choice = None
        while not valid_choice:
            # Check for timeout (e.g., 10 seconds)
            if time.time() - start_time > 60:
                tts.say("I'm not getting any input. Let's try again from the start.")
                reset_nao()
                break

            tts.say("What do you choose? Rock, paper, or scissors?")
            asr.subscribe("rps_game")
            time.sleep(5)  # Increased pause for speech recognition
            wordRecognized = memory.getData("WordRecognized")

            asr.unsubscribe("rps_game")

            if wordRecognized and wordRecognized[0] in vocabulary:
                user_choice = wordRecognized[0].split()[-1]
                valid_choice = True
                tts.say("You chose " + user_choice + ".")
            else:
                failed_attempts += 1
                if failed_attempts >= 3:
                    tts.say("I'm having trouble understanding. Please try speaking clearly or try again later.")
                else:
                    tts.say("I didn't quite get that. Please try again.")

        # Determine the winner and update scores 
        if nao_choice == user_choice:
            tts.say("It's a tie! Great minds think alike, don't they?")
        elif (nao_choice == "rock" and user_choice == "scissors") or \
             (nao_choice == "paper" and user_choice == "rock") or \
             (nao_choice == "scissors" and user_choice == "paper"):
            win_phrases = [
                "Yes! I win this round!",
                "Woohoo! I'm on fire!",
                "I got you this time! Better luck next round!"
            ]
            animated_speech.say("^start(animations/Stand/Emotions/Positive/Excited_1) {} {} ^wait(animations/Stand/Emotions/Positive/Excited_1)".format(random.choice(win_phrases), random.choice(happy_expressions)))
            nao_wins += 1
        else:
            lose_phrases = [
                "You got me! Well played!",
                "Oh no! You're too good!",
                "I'll get you next time!"
            ]
            animated_speech.say("^start(animations/Stand/Emotions/Negative/Sad_1) {} {} ^wait(animations/Stand/Emotions/Negative/Sad_1)".format(random.choice(lose_phrases), random.choice(sad_expressions)))
            user_wins += 1

        rounds_played += 1

    # Announce final score and send-off
    if nao_wins > user_wins:
        tts.say("I win the game! But you played really well. Want a rematch sometime?")
    elif nao_wins < user_wins:
        tts.say("Congratulations! You win the game! You're a rock-paper-scissors master!")
    else:
        tts.say("It's a tie game! We're evenly matched. How about another game to break the tie?")

    tts.say("The final score is: I have {} wins, and you have {} wins. Thanks for playing with me!".format(nao_wins, user_wins))
    tts.say("I had a lot of fun. I hope you enjoyed our game too!")
    posture.goToPosture("SitRelax", 0.5)


# Start the game in a Choreographe box
play_rps()