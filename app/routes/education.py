"""
Education Routes
Learning hub for mastering hip-hop skills
"""
from flask import Blueprint, render_template

education_bp = Blueprint('education', __name__)

# Static content for now. In a real app, this might be in a DB or Markdown files.
MODULES = {
    "rhyme-mastery": {
        "title": "Rhyme Scheme Architecture",
        "category": "Mastery",
        "description": "Deconstructing the mathematical scaffolding of elite lyricism.",
        "content": """
            <div class="masterclass-section">
                <h3>The Theory: Rhyme as Percussion</h3>
                <p>Don't think of rhyme just as "matching sounds." <strong>Rhyme is percussion.</strong> It creates the grid that listeners nod their heads to. When you place a rhyme, you are placing a snare drum in the listener's ear.</p>
                <div class="pro-tip">
                    <strong>Master's Mindset:</strong> Great rappers don't just find words that rhyme; they find the *rhythm* of the rhyme first, then fill in the words. Use "scatting" (da-da-DA, da-da-DA) to find the pocket before writing a single word.
                </div>
            </div>

            <div class="masterclass-section">
                <h3>Case Study: The "Compound Multi"</h3>
                <p>The hallmark of a virtuoso is the Multi-Syllabic Rhyme. It turns a nursery rhyme pattern into a complex rhythmic texture.</p>
                
                <div class="lyrics-breakdown">
                    <h4>Eminem - "Lose Yourself" (Deconstructed)</h4>
                    <p class="bar">"His <span class="rhyme-a">palms</span> are <span class="rhyme-b">swea-ty</span>, <span class="rhyme-c">knees weak</span>, <span class="rhyme-a">arms</span> are <span class="rhyme-b">hea-vy</span>"</p>
                    <p class="bar">"There's <span class="rhyme-d">vo-mit</span> on his <span class="rhyme-e">swea-ter</span> al-<span class="rhyme-b">rea-dy</span>, <span class="rhyme-d">mom's spa</span>-<span class="rhyme-e">ghe-tti</span>"</p>
                </div>
                <p><strong>Analysis:</strong> Notice the internal density. He doesn't wait for the end of the line. <span class="rhyme-b">Swea-ty</span>, <span class="rhyme-b">Hea-vy</span>, <span class="rhyme-b">Rea-dy</span>, <span class="rhyme-e">Ghe-tti</span> all anchor the "E" sound, while <span class="rhyme-a">Palms/Arms</span> and <span class="rhyme-d">Vomit/Mom's</span> provide syncopated counter-rhythms.</p>
            </div>

            <div class="masterclass-section">
                <h3>The Studio Drill</h3>
                <div class="drill-card">
                    <h4>Exercise: The 4-Syllable Ladder</h4>
                    <ol>
                        <li>Pick a 4-syllable phrase (e.g., "California").</li>
                        <li>Find 5 phrases that rhyme with the <em>entire</em> structure (Stress: da-da-DA-da).</li>
                        <li><strong>Target:</strong> "Paranoia," "Stall or join ya," "Call a lawyer," "Small begonia."</li>
                        <li>Write 4 bars using these as the anchors.</li>
                    </ol>
                </div>
            </div>
            
            <div class="resources-section">
                <h4>Required Listening</h4>
                <ul>
                    <li><a href="https://www.youtube.com/watch?v=sBvngg87998" target="_blank">Big Pun - "Twinz" (The 'Little Italy' Scheme)</a></li>
                    <li><a href="https://www.youtube.com/watch?v=ThlhSnxrU7o" target="_blank">MF DOOM - "Accordion" (Non-stop internal rhymes)</a></li>
                </ul>
            </div>
        """
    },
    "science-of-flow": {
        "title": "Kinetic Flow Dynamics",
        "category": "Technique",
        "description": "Manipulating time, pockets, and silence for maximum impact.",
        "content": """
            <div class="masterclass-section">
                <h3>The Theory: The Grid & The Swing</h3>
                <p>A DAW (Digital Audio Workstation) visualizes music on a grid of bars and beats. <strong>Flow is how you traverse this grid.</strong></p>
                <ul>
                    <li><strong>Straight Grid:</strong> Hitting every 1/16th note perfectly (Robotic, Kraftwerk-style).</li>
                    <li><strong>Swing:</strong> Deliberately delaying the even notes to create a "human" feel (J Dilla, Jazz, Boom Bap).</li>
                </ul>
                <div class="pro-tip">
                    <strong>Master's Mindset:</strong> Silence is a note. A rest (pause) communicates confidence. If you rap non-stop, you sound anxious. If you pause, you force the audience to lean in.
                </div>
            </div>

            <div class="masterclass-section">
                <h3>Case Study: The "Triplet" (Migos Flow)</h3>
                <p>The signature sound of modern Trap. Breaking a 4/4 beat into groups of 3.</p>
                
                <div class="lyrics-breakdown">
                     <h4>Migos - "Versace" Pattern</h4>
                     <p class="bar">ver-<span class="rhyme-a">sa-ce</span> ver-<span class="rhyme-a">sa-ce</span> ver-<span class="rhyme-a">sa-ce</span> ver-<span class="rhyme-a">sa-ce</span></p>
                </div>
                <p><strong>Analysis:</strong> It creates a rolling, galloping feeling that creates high energy. It fights against the square nature of the drum beat, creating tension and release.</p>
            </div>

            <div class="masterclass-section">
                <h3>Case Study: "Behind the Beat" (Lazy Flow)</h3>
                <p>Used by icons like Snoop Dogg, Jay-Z, and J Cole. You rap milliseconds <em>after</em> the snare hits.</p>
                <div class="lyrics-breakdown">
                    <p><strong>Effect:</strong> It sounds effortless, cool, and conversational. It says "I control time; time doesn't control me."</p>
                </div>
            </div>

            <div class="masterclass-section">
                <h3>The Studio Drill</h3>
                <div class="drill-card">
                    <h4>Exercise: The Ten-Speed Gearbox</h4>
                    <p>Rap the same 4 bars over the same beat in three different ways:</p>
                    <ol>
                        <li><strong>Halftime:</strong> Very slow, lots of space.</li>
                        <li><strong>In the Pocket:</strong> Standard conversation pace.</li>
                        <li><strong>Doubletime:</strong> Twice as fast as the beat.</li>
                    </ol>
                    <p><em>Record yourself and listen back. Which one "sat" best in the mix?</em></p>
                </div>
            </div>
        """
    },
    "song-structure": {
        "title": "Song Structure Architecture",
        "category": "Arrangement",
        "description": "From 'Intro' to 'Outro': How to build a sonic journey.",
        "content": """
            <div class="masterclass-section">
                <h3>The Theory: Energy Management</h3>
                <p>A song is an emotional rollercoaster. You cannot stay at 100% intensity for 3 minutes. You must build, release, and rebuild tension.</p>
                
                <h4>The Standard Pop/Rap Formula</h4>
                <div class="structure-diagram">
                    <span class="block intro">Intro (4-8)</span> → 
                    <span class="block hook">Chorus (8-16)</span> → 
                    <span class="block verse">Verse 1 (16)</span> → 
                    <span class="block hook">Chorus (8)</span> → 
                    <span class="block verse">Verse 2 (16)</span> → 
                    <span class="block bridge">Bridge (8)</span> → 
                    <span class="block hook">Chorus (8-16)</span> → 
                    <span class="block outro">Outro</span>
                </div>
            </div>

            <div class="masterclass-section">
                <h3>Component Analysis</h3>
                <ul>
                    <li><strong>The Hook (Chorus):</strong> The thesis statement. Simple, melodic, repetitive. This is what they sing in the stadium.</li>
                    <li><strong>The Verse:</strong> The details. The story. The proof of your skill. This is for the true fans.</li>
                    <li><strong>The Bridge:</strong> The "twist." A change in flow, melody, or perspective. It cleans the palette before the final Chorus.</li>
                </ul>
                <div class="pro-tip">
                    <strong>Master's Mindset:</strong> Don't bore us, get to the Chorus. In the streaming era, if you don't catch attention in the first 10 seconds (Intro), you've lost the stream.
                </div>
            </div>

            <div class="masterclass-section">
                <h3>Case Study: "Sicko Mode" (Anti-Structure)</h3>
                <p>Travis Scott's "Sicko Mode" broke all rules. It has three different beats, no clear verse/chorus structure, and sudden tempo changes.</p>
                <p><strong>Lesson:</strong> Once you master the rules, verify you can break them effectively. Structure serves the <em>vibe</em>, not the other way around.</p>
            </div>
        """
    },
    "hip-hop-history": {
        "title": "Legacy: The 50-Year Blueprint",
        "category": "History",
        "description": "Understanding the giants on whose shoulders you stand.",
        "content": """
            <div class="masterclass-section">
                <h3>Timeline of Innovation</h3>
                
                <div class="timeline-item">
                    <h4>1973-1979: The Park Jams (The Loop)</h4>
                    <p><strong>Innovation:</strong> The Breakbeat.</p>
                    <p>DJ Kool Herc extended the funkiest parts of records. MCs like Coke La Rock only shouted phrases ("Yes yes y'all!") to keep the party moving.</p>
                </div>

                <div class="timeline-item">
                    <h4>1987-1992: The Golden Era (The Sample)</h4>
                    <p><strong>Innovation:</strong> Sampling & Lyricism.</p>
                    <p>Marley Marl and Pete Rock treated samplers as instruments. <br><strong>Rakim</strong> invented complex internal rhyme schemes, moving rap from AABB simplistic patterns to jazz-like complexity.</p>
                </div>

                <div class="timeline-item">
                    <h4>1992-1997: G-Funk & Boom Bap (The Groove)</h4>
                    <p><strong>West Coast:</strong> Dr. Dre introduced live instrumentation and synthesizers (G-Funk). <br><strong>East Coast:</strong> DJ Premier and Wu-Tang perfected gritty, lo-fi drum chops.</p>
                </div>

                <div class="timeline-item">
                    <h4>2010s: The Melodic Shift (The Vibe)</h4>
                    <p><strong>Innovation:</strong> Auto-Tune & Emotion.</p>
                    <p>Kanye West (808s) and T-Pain normalized singing rappers. Drake and Future dissolved the line between rapping and singing entirely, creating "Melodic Rap."</p>
                </div>
            </div>

            <div class="resources-section">
                <h4>Mastery Library</h4>
                <ul>
                    <li><a href="https://www.netflix.com/title/80141782" target="_blank">Hip-Hop Evolution (Netflix)</a> - Essential viewing.</li>
                    <li><a href="https://www.youtube.com/watch?v=VRPxyaoCNtk" target="_blank">Sample Breakdown: How J Dilla humanized the MPC</a></li>
                </ul>
            </div>
        """
    },
    "metaphor-mastery": {
        "title": "Advanced Lyrical Devices",
        "category": "Writing",
        "description": "Weighted words, double entendres, and narrative arcs.",
        "content": """
            <div class="masterclass-section">
                <h3>The Theory: "Stank Face" Bars</h3>
                <p>A "Stank Face" bar is a line so clever or nasty that the listener involuntarily grimaces. This usually comes from a <strong>Double Entendre</strong> or a <strong>Homophone Scheme</strong>.</p>
            </div>

            <div class="masterclass-section">
                <h3>Technique: The Pivot</h3>
                <p>Using a word that changes meaning halfway through the setup.</p>
                
                <div class="lyrics-breakdown">
                    <h4>Jay-Z - "Diamonds from Sierra Leone"</h4>
                    <p class="bar">"I'm not a <strong>businessman</strong>..."</p>
                    <p class="explanation">(Listener expects: He is an artist, not a suit.)</p>
                    <p class="bar">"...I'm a <strong>business</strong>, man."</p>
                    <p class="explanation">(Twist: He is the enterprise itself.)</p>
                </div>
            </div>

            <div class="masterclass-section">
                <h3>Technique: The Extended Metaphor</h3>
                <p>Carrying a single comparison across 4, 8, or 16 bars.</p>
                
                <div class="lyrics-breakdown">
                    <h4>Common - "I Used to Love H.E.R."</h4>
                    <p><strong>Concept:</strong> He talks about a girl he grew up with, how she changed, how she sold out to corporate guys in LA.</p>
                    <p><strong>Reveal:</strong> The "Girl" was Hip-Hop music itself. The entire song is a personification metaphor.</p>
                </div>
            </div>

            <div class="masterclass-section">
                <h3>The Studio Drill</h3>
                <div class="drill-card">
                    <h4>Exercise: Object Personification</h4>
                    <ol>
                        <li>Pick an object (e.g., A Gun, Money, A Microphone, A Car).</li>
                        <li>Write 8 bars describing it as if it were a <em>person</em>.</li>
                        <li>Do not name the object. Let the listener guess.</li>
                    </ol>
                </div>
            </div>
        """
    }
}

@education_bp.route('/')
def index():
    """Education Dashboard"""
    return render_template('education/index.html', modules=MODULES)

@education_bp.route('/module/<slug>')
def view_module(slug):
    """View specific module"""
    module = MODULES.get(slug)
    if not module:
        return render_template('404.html'), 404
        
    return render_template('education/module.html', module=module, slug=slug)
