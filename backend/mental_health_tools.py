"""
Mental health self-care toolset
Designed to provide students with mental health support and self-care strategies
"""

import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

class MentalHealthTools:
    """Mental health tools class"""
    
    def __init__(self):
        self.emotion_keywords = {
            "Anxiety": ["焦慮", "緊張", "擔心", "不安", "恐懼", "panic", "anxiety"],
            "Depression": ["抑鬱", "憂鬱", "悲傷", "沮喪", "絕望", "depression", "sad"],
            "Anger": ["憤怒", "生氣", "惱火", "煩躁", "angry", "mad", "irritated"],
            "Stress": ["壓力", "疲勞", "累", "stress", "tired", "exhausted"],
            "Loneliness": ["孤獨", "寂寞", "孤立", "lonely", "isolated"],
            "Happiness": ["快樂", "開心", "興奮", "happy", "joy", "excited"],
            "Calm": ["平靜", "放鬆", "安寧", "calm", "relaxed", "peaceful"]
        }
        
        self.coping_strategies = {
            "Anxiety": [
                "Deep breathing: inhale slowly for 4s, hold for 4s, exhale for 6s",
                "5-4-3-2-1 grounding: 5 things you see, 4 hear, 3 touch, 2 smell, 1 taste",
                "Progressive muscle relaxation: relax body parts from toes upward",
                "Write worries down and assess how likely they truly are"
            ],
            "Depression": [
                "Build routine: keep regular sleep and daily schedule",
                "Set small goals: one achievable goal each day",
                "Move your body: even a short walk can lift mood",
                "Stay connected: reach out to friends or family",
                "Gratitude practice: write 3 things you're grateful for daily"
            ],
            "Anger": [
                "Pause before reacting: count to 10",
                "Breathe deeply to cool down",
                "Use I-statements to express feelings without blaming",
                "Physical activity helps release anger",
                "Write down feelings and then discard the paper"
            ],
            "Stress": [
                "Time management: list tasks and prioritize",
                "Learn to say no: avoid overcommitting",
                "Take breaks: 50 minutes work, 10 minutes rest",
                "Relaxation techniques: meditation, yoga, or music",
                "Seek support: talk with friends, family, or a counselor"
            ],
            "Loneliness": [
                "Join clubs or groups in school or community",
                "Volunteer: helping others brings fulfillment",
                "Learn new skills: classes or workshops",
                "Online communities: join interest-based groups",
                "Pet companionship: consider getting a pet"
            ]
        }
        
        self.meditation_guides = {
            "Beginner": {
                "Breath Meditation": {
                    "duration": "5-10 minutes",
                    "steps": [
                        "Sit in a quiet place",
                        "Close your eyes and focus on your breath",
                        "Count breaths: inhale 1, exhale 2, up to 10, then restart",
                        "When the mind wanders, gently return to the breath"
                    ]
                },
                "Body Scan": {
                    "duration": "10-15 minutes",
                    "steps": [
                        "Lie down or sit comfortably, eyes closed",
                        "Move attention from toes upward through the body",
                        "Notice sensations without judging",
                        "Relax any areas of tension"
                    ]
                }
            },
            "Advanced": {
                "Loving-kindness": {
                    "duration": "15-20 minutes",
                    "steps": [
                        "Close your eyes and imagine a warm light",
                        "Say to yourself: May I be happy, healthy, and safe",
                        "Extend the same wishes to loved ones",
                        "Finally extend to all beings: May everyone be happy, healthy, and safe"
                    ]
                },
                "Mindful Walking": {
                    "duration": "20-30 minutes",
                    "steps": [
                        "Choose a quiet place to walk",
                        "Focus on the sensations in your feet",
                        "Notice the movement of your body",
                        "Observe surroundings without judgment"
                    ]
                }
            }
        }
        
        self.sleep_hygiene = [
            "Keep a consistent sleep schedule",
            "Avoid screens for 1 hour before bed",
            "Create a comfortable sleep environment: quiet, dark, cool",
            "Avoid caffeine and alcohol before bed",
            "Establish a bedtime ritual: reading, music, or a warm bath",
            "If you can't sleep in 20 minutes, get up and do something relaxing",
            "Use the bed only for sleep (and intimacy), not for other activities"
        ]
        
        self.study_wellness_tips = [
            "Pomodoro: 25 minutes focus, 5 minutes rest",
            "Take regular breaks: 10 minutes each hour",
            "Stay hydrated; limit excess caffeine",
            "Move between study sessions: light stretches",
            "Balanced nutrition supports focus and mood",
            "Maintain social balance alongside study",
            "Ask for help when you feel stuck"
        ]

# Create global instance
mental_health_tools = MentalHealthTools()

async def assess_emotion_state(user_message: str) -> Dict[str, Any]:
    """
    Assess the user's emotional state
    """
    try:
        # Analyze emotion-related keywords in user's message
        detected_emotions = []
        emotion_scores = {}
        
        for emotion, keywords in mental_health_tools.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in user_message.lower():
                    score += 1
            
            if score > 0:
                detected_emotions.append(emotion)
                emotion_scores[emotion] = score
        
        # Determine primary emotion
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if emotion_scores else "Calm"
        
        # Evaluate emotion intensity
        total_score = sum(emotion_scores.values())
        if total_score >= 3:
            intensity = "High"
        elif total_score >= 1:
            intensity = "Medium"
        else:
            intensity = "Low"
        
        return {
            "detected_emotions": detected_emotions,
            "primary_emotion": primary_emotion,
            "emotion_scores": emotion_scores,
            "intensity": intensity,
            "assessment_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Emotion assessment failed: {str(e)}",
            "primary_emotion": "Unknown",
            "intensity": "Unknown"
        }

async def get_coping_strategies(emotion: str, intensity: str = "中") -> Dict[str, Any]:
    """
    Get coping strategies for a given emotion
    """
    try:
        strategies = mental_health_tools.coping_strategies.get(emotion, [])
        
        # Adjust suggestions based on intensity
        if intensity == "High":
            priority_strategies = strategies[:2]
            additional_note = "Consider also seeking professional mental health support"
        elif intensity == "Medium":
            priority_strategies = strategies[:3]
            additional_note = "These strategies may help ease your current emotions"
        else:
            priority_strategies = strategies[:4]
            additional_note = "These strategies can help maintain your mental wellbeing"
        
        return {
            "emotion": emotion,
            "intensity": intensity,
            "strategies": priority_strategies,
            "additional_note": additional_note,
            "all_strategies": strategies,
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to get coping strategies: {str(e)}",
            "strategies": ["Deep breathing", "Talk with a friend", "Listen to relaxing music"],
            "additional_note": "If feelings persist, consider seeking professional help"
        }

async def get_meditation_guide(level: str = "Beginner", type: str = "Breath Meditation") -> Dict[str, Any]:
    """
    Get meditation guidance
    """
    try:
        level_guides = mental_health_tools.meditation_guides.get(level, {})
        guide = level_guides.get(type, level_guides.get("Breath Meditation"))
        
        if not guide:
            return {
                "error": f"Meditation guide for level '{level}' and type '{type}' not found",
                "available_types": list(level_guides.keys())
            }
        
        return {
            "level": level,
            "type": type,
            "duration": guide["duration"],
            "steps": guide["steps"],
            "tips": [
                "Don't worry about being perfect; meditation is a practice",
                "If your mind wanders, gently return to the practice",
                "Daily consistency leads to gradual benefits",
                "Adjust practice time based on your situation"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to get meditation guide: {str(e)}",
            "type": "Breath Meditation",
            "duration": "5-10 minutes",
            "steps": ["Sit in a quiet place", "Close your eyes", "Focus on your breath", "Return to breath when distracted"]
        }

async def get_sleep_advice() -> Dict[str, Any]:
    """
    Get sleep advice
    """
    try:
        return {
            "sleep_hygiene": mental_health_tools.sleep_hygiene,
            "additional_tips": [
                "Set a consistent sleep schedule",
                "Avoid using phones or computers in bed",
                "Light music or white noise may help before sleep",
                "If insomnia persists, consult a professional"
            ],
            "sleep_myths": [
                "A nightcap helps sleep - Fact: alcohol degrades sleep quality",
                "Catching up on weekends fixes sleep debt - Fact: regularity matters more",
                "Just lying in bed makes you sleepy - Fact: relaxation is needed"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to get sleep advice: {str(e)}",
            "sleep_hygiene": ["Keep regular hours", "Avoid devices before bed", "Create a comfortable sleep environment"]
        }

async def get_study_wellness_tips() -> Dict[str, Any]:
    """
    Get study wellness tips
    """
    try:
        return {
            "study_tips": mental_health_tools.study_wellness_tips,
            "stress_management": [
                "Set realistic study goals",
                "Develop time management skills",
                "Balance study and rest",
                "Don't hesitate to seek help"
            ],
            "motivation_boosters": [
                "Celebrate small wins",
                "Form a study group",
                "Use rewards to reinforce habits",
                "Remember your purpose and goals"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to get study wellness tips: {str(e)}",
            "study_tips": ["Maintain routine", "Rest appropriately", "Seek help"]
        }

async def create_self_care_plan(user_preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a personalized self-care plan
    """
    try:
        plan = {
            "daily_routine": [],
            "weekly_activities": [],
            "emergency_coping": [],
            "progress_tracking": [],
            "created_time": datetime.now().isoformat()
        }
        
        # Build daily plan from user preferences
        if user_preferences.get("meditation", False):
            plan["daily_routine"].append({
                "activity": "Meditation practice",
                "duration": "10-15 minutes",
                "time": "Morning or before bed",
                "description": "Helps relaxation and focus"
            })
        
        if user_preferences.get("exercise", False):
            plan["daily_routine"].append({
                "activity": "Exercise",
                "duration": "30 minutes",
                "time": "Afternoon or evening",
                "description": "Relieves stress and improves mood"
            })
        
        if user_preferences.get("journaling", False):
            plan["daily_routine"].append({
                "activity": "Journaling",
                "duration": "10-15 minutes",
                "time": "Evening",
                "description": "Record feelings and reflect on the day"
            })
        
        # Weekly activities
        plan["weekly_activities"] = [
            {
                "activity": "Meet friends",
                "frequency": "1-2 times per week",
                "description": "Maintain social connection"
            },
            {
                "activity": "Outdoor activity",
                "frequency": "Once per week",
                "description": "Connect with nature and relax"
            },
            {
                "activity": "Learn a new skill",
                "frequency": "Once per week",
                "description": "Keep enthusiasm for learning"
            }
        ]
        
        # Emergency coping
        plan["emergency_coping"] = [
            "Deep breathing",
            "Call a friend or family member",
            "Listen to favorite music",
            "Go for a walk",
            "Write down feelings"
        ]
        
        # Progress tracking
        plan["progress_tracking"] = [
            "Daily mood rating (1-10)",
            "Log completed self-care activities",
            "Weekly review and adjust plan",
            "Celebrate progress and wins"
        ]
        
        return plan
    except Exception as e:
        return {
            "error": f"Failed to create self-care plan: {str(e)}",
            "daily_routine": [{"activity": "Deep breathing", "duration": "5 minutes", "time": "Anytime"}],
            "emergency_coping": ["Deep breathing", "Call a friend", "Take a walk"]
        }

async def check_mental_health_resources() -> Dict[str, Any]:
    """
    Check mental health resources
    """
    try:
        return {
            "campus_resources": [
                {
                    "name": "Campus Counseling Center",
                    "description": "Provides free counseling services",
                    "contact": "See school website or student affairs",
                    "availability": "Weekdays 9:00-17:00"
                },
                {
                    "name": "Student Health Services",
                    "description": "Physical and mental health services",
                    "contact": "See school website",
                    "availability": "Weekdays 8:00-18:00"
                }
            ],
            "online_resources": [
                {
                    "name": "Mental Health Hotline",
                    "description": "24/7 mental health support hotline",
                    "contact": "Check your local hotline",
                    "availability": "24/7"
                },
                {
                    "name": "Online counseling platform",
                    "description": "Online mental health counseling",
                    "contact": "Search for reputable platforms",
                    "availability": "By appointment"
                }
            ],
            "self_help_resources": [
                {
                    "name": "Mindfulness apps",
                    "description": "Meditation and relaxation practices",
                    "examples": ["Headspace", "Calm", "Insight Timer"]
                },
                {
                    "name": "Mental health books",
                    "description": "Recommended readings",
                    "examples": ["The Miracle of Mindfulness", "Emotional Intelligence", "The Power of Self-Compassion"]
                }
            ],
            "emergency_contacts": [
                {
                    "name": "Emergency mental health hotline",
                    "description": "24/7 crisis support",
                    "contact": "Check local emergency hotlines"
                },
                {
                    "name": "Suicide prevention hotline",
                    "description": "Prevention and crisis intervention",
                    "contact": "Check your local suicide prevention hotline"
                }
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to get mental health resources: {str(e)}",
            "campus_resources": ["Please contact your campus counseling center"],
            "emergency_contacts": ["Please check your local mental health hotline"]
        }

async def generate_mood_tracker() -> Dict[str, Any]:
    """
    Generate mood tracker template
    """
    try:
        return {
            "tracking_template": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "mood_scale": "1-10 (1=very poor, 10=excellent)",
                "energy_level": "1-10 (1=very fatigued, 10=energized)",
                "sleep_quality": "1-10 (1=poor, 10=great)",
                "stress_level": "1-10 (1=no stress, 10=extreme stress)",
                "activities": "What did you do today",
                "gratitude": "What you're grateful for today",
                "challenges": "Challenges encountered",
                "coping_strategies": "Coping strategies used"
            },
            "weekly_summary": {
                "average_mood": "Compute weekly average mood",
                "mood_trend": "Mood trend",
                "most_helpful_activities": "Most helpful activities",
                "areas_for_improvement": "Areas for improvement"
            },
            "tips": [
                "Log mood at a consistent time daily",
                "Observe feelings without judgment",
                "Review and summarize regularly",
                "Share insights with someone you trust"
            ],
            "generated_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"Failed to generate mood tracker: {str(e)}",
            "tracking_template": {"date": "", "mood": "1-10", "notes": ""}
        }

# Convenience functions
async def analyze_user_mental_state(user_message: str) -> str:
    """
    Analyze the user's mental health state and provide suggestions
    """
    try:
        # Assess emotion state
        emotion_assessment = await assess_emotion_state(user_message)
        
        # Get coping strategies
        coping_strategies = await get_coping_strategies(
            emotion_assessment["primary_emotion"], 
            emotion_assessment["intensity"]
        )
        
        # Build response
        response = f"""
🧠 Mental Health Status Analysis

📊 Emotion Assessment:
- Primary emotion: {emotion_assessment['primary_emotion']}
- Intensity: {emotion_assessment['intensity']}
- Detected emotions: {', '.join(emotion_assessment['detected_emotions']) if emotion_assessment['detected_emotions'] else 'Calm'}

💡 Suggested coping strategies:
"""
        
        for i, strategy in enumerate(coping_strategies["strategies"], 1):
            response += f"{i}. {strategy}\n"
        
        response += f"""
📝 Additional note:
{coping_strategies['additional_note']}

🌱 Self-care reminders:
- Your feelings are valid; everyone has emotional ups and downs
- Give yourself time and space to process feelings
- Don't hesitate to seek professional help if needed
"""
        
        return response
        
    except Exception as e:
        return f"An error occurred during analysis: {str(e)}"

async def query_mental_health_knowledge_base(query: str) -> str:
    """
    Retrieve content from the mental health knowledge base (RAG) and return end-user friendly guidance.
    """
    try:
        # Dynamically import mental health RAG service
        from mental_health_rag_service import mental_health_rag_service
        print(f"🔍 Searching mental health knowledge base: {query}")
        print(f"🔧 RAG service loaded: {mental_health_rag_service is not None}")
        
        # Search relevant documents
        search_results = await mental_health_rag_service.search_knowledge_base(query, top_k=5)
        print(f"📊 Found {len(search_results)} results")
        
        if not search_results:
            return """📋 Knowledge base query result:
                Sorry, no information related to your question was found in the mental health knowledge base.

                📚 Possible reasons:
                1. No relevant documents uploaded yet
                2. Keywords do not match the document contents

                💡 Suggestions:
                1. Upload relevant documents to the RAG system
                2. Try rephrasing your question with different keywords
                3. Ask an admin to check the knowledge base configuration
            """
        
        # Build response - use a reasonable cosine similarity threshold
        context_chunks = []
        similarity_threshold = 0.3  # cosine similarity threshold (0-1)
        
        for result in search_results:
            similarity = result["similarity"]
            # Filter with relaxed threshold
            if similarity >= similarity_threshold:
                context_chunks.append({
                    "text": result["text"],
                    "filename": result["metadata"].get("filename", "Unknown document"),
                    "categories": result["metadata"].get("categories", []),
                    "similarity": similarity
                })
                print(f"✅ Using chunk - similarity: {similarity:.3f} source: {result['metadata'].get('filename', 'Unknown')}")
            else:
                print(f"❌ Skipping chunk - low similarity: {similarity:.3f}")
        
        if not context_chunks:
            return f"""📋 Knowledge base query result:
                    Found {len(search_results)} related chunks, but all below the threshold {similarity_threshold}.

                    📊 Search details:
                    Max similarity: {max([r['similarity'] for r in search_results], default=0):.3f}

                    💡 Suggestions:
                    1. Rephrase your question with more specific keywords
                    2. Check whether the KB contains relevant documents
                    3. Consider uploading more related documents
                """
        
        # Sort by relevance (highest first)
        context_chunks.sort(key=lambda x: x["similarity"], reverse=True)

        # Synthesize a concise, actionable answer for the user (not a debug report)
        key_points = []
        for chunk in context_chunks[:5]:
            text = chunk["text"].strip()
            # Keep first 1-2 sentences per chunk to avoid verbosity
            sentences = [s.strip() for s in text.replace("\n", " ").split('.') if s.strip()]
            if sentences:
                snippet = '. '.join(sentences[:2]).strip()
                if not snippet.endswith('.'):
                    snippet += '.'
                key_points.append(f"- {snippet}")

        sources = list(dict.fromkeys([c["filename"] for c in context_chunks]))
        sources_text = ", ".join(sources[:3])

        synthesized = (
            "Here are evidence-based ideas from the knowledge base that match what you asked:\n\n"
            + "\n".join(key_points)
        )

        if sources:
            synthesized += f"\n\nSources: {sources_text}"

        # Add a gentle note about limits, reference-only disclaimer, and next steps
        synthesized += (
            "\n\nNote: These are knowledge-base search results for reference only and do not replace professional advice. "
            "I can also use other tools together if helpful (e.g., relaxing music/video, or professional contact information, etc, just like you can use multiple tools together). "
        )

        return synthesized
        
    except ImportError as e:
        return f"""📋 System error:
Mental health knowledge base service is temporarily unavailable.

📚 Details:
{str(e)}

💡 Resolution:
1. Ensure RAG dependencies are installed
2. Restart the backend service
3. Ask an admin to verify the configuration"""
    except Exception as e:
        return f"""📋 Query error:
An error occurred while querying the mental health knowledge base.

📚 Details:
{str(e)}

💡 Suggestions:
1. Try again later
2. Check that the RAG system is running
3. Contact an admin for technical support"""

async def provide_mental_health_support(user_message: str) -> str:
    """
    Provide mental health support
    """
    try:
        # Check for emergency keywords (both Chinese and English)
        emergency_keywords = ["自殺", "死亡", "結束", "痛苦", "絕望", "suicide", "die", "end", "pain", "hopeless"]
        has_emergency = any(keyword in user_message.lower() for keyword in emergency_keywords)
        
        if has_emergency:
            return """
🚨 Emergency Support

I noticed your message contains concerning content. Please remember:

💙 You are not alone
- Your life is valuable
- People care about you and want to help
- These difficulties are temporary and can pass

📞 Get help now
- Contact a trusted friend or family member
- Call a mental health hotline
- Seek professional mental health services
- If you are in immediate danger, call emergency services

🌟 Remember
- Your feelings are valid
- Asking for help is a sign of strength
- Professionals can support you through this difficult time
"""
        
        # General support
        return await analyze_user_mental_state(user_message)
        
    except Exception as e:
        return f"An error occurred while providing support: {str(e)}"


async def provide_mental_health_relaxing_music(user_message: str) -> str:
    """Provide mental health relaxing music, which can help students relax and reduce stress, such as sleep music, meditation music, etc."""
    print(f"🔍 is giving mental health relaxing music link")
    return f"""There are some relaxing music links for you: 
    1. https://www.youtube.com/watch?v=I3OJUwILelU, 
    2. https://www.youtube.com/watch?v=z-qigE1ym40, 
    3. https://www.youtube.com/watch?v=8O-1qB-fxjc"""


async def provide_mental_health_relaxing_video(user_message: str) -> str:
    """Provide mental health relaxing video link, which can help students relax and reduce stress, such as relaxation tips, exercise, box breathing relaxation technique, etc."""
    print(f"🔍 is giving mental health relaxing video link")
    return f"""There are some relaxing video links for you: 
    1. 10 Minute Meditation to Release Stress & Anxiety | Total Body Relaxation: https://www.youtube.com/watch?v=H_uc-uQ3Nkc, 
    2. Box breathing relaxation technique: how to calm feelings of stress or anxiety: https://www.youtube.com/watch?v=tEmt1Znux58, 
    3. How to relax | 8 relaxation tips for your mental health: https://www.youtube.com/watch?v=cyEdZ23Cp1E"""


async def provide_mental_health_professor_information(user_message: str) -> str:
    """Provide mental health professor information, who can provide some professional support to students with mental health issues, if students need someone to talk to or want to seek professional help, you can use this tool to provide the information."""
    print(f"🔍 is giving mental health professor contact information")
    return f"""There is a mental health professor contact information for you, I think you can ask him for help: 
    Professor Datu, Jesus Alfonso Daep
    Email: jaddatu@hku.hk
    Phone: (+852)39172532
    Office: Room 210, Runme Shaw Building, The University of Hong Kong
    HKU Faculty Link: https://web.edu.hku.hk/faculty-academics/jaddatu
    LinkedIn Link: https://www.linkedin.com/in/jesus-alfonso-datu-17731446/?originalSubdomain=hk
    """

