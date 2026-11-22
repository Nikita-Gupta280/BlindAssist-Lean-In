
import { useState, useEffect, useRef } from "react";
import {
  Eye, Camera, Activity, Volume2, Shield,
  AlertTriangle, Footprints, Radio, CircleDot, Play, Pause,
  Languages, Navigation, Scan, Waves
} from "lucide-react";
import "./App.css";

const API = "https://programming-annual-paxil-creek.trycloudflare.com";

const HINDI_LABELS = {
  person: "व्यक्ति",
  chair: "कुर्सी",
  stairs: "सीढ़ियाँ",
  stair: "सीढ़ियाँ",
  door: "दरवाज़ा",
  pothole: "गड्ढा",
  bottle: "बोतल",
  car: "गाड़ी",
  motorcycle: "मोटरसाइकिल",
  bicycle: "साइकिल",
  bus: "बस",
  truck: "ट्रक",
  dog: "कुत्ता",
  bench: "बेंच",
  backpack: "बैग",
  handbag: "हैंडबैग",
  suitcase: "सूटकेस",
  umbrella: "छाता",
  table: "मेज़",
  cell_phone: "मोबाइल फ़ोन",
  phone: "मोबाइल फ़ोन",
  laptop: "लैपटॉप",
  television: "टीवी",
  tv: "टीवी",
  book: "किताब",
  cup: "कप",
  dining_table: "डाइनिंग टेबल",
  potted_plant: "गमला",
  sink: "सिंक",
  refrigerator: "फ्रिज",
  toilet: "शौचालय",
  traffic_light: "ट्रैफिक लाइट",
  stop_sign: "स्टॉप साइन",
};

const HINDI_DIRECTIONS = {
  ahead: "सामने",
  front: "सामने",
  center: "बीच में",
  left: "बाईं ओर",
  right: "दाईं ओर",
  "ahead-left": "सामने बाईं ओर",
  "ahead-right": "सामने दाईं ओर",
  "front-left": "सामने बाईं ओर",
  "front-right": "सामने दाईं ओर",
  unknown: "आपके आसपास",
};

export default function App() {
  const [running, setRunning] = useState(false);
  const [language, setLanguage] = useState("English");
  const [intensity, setIntensity] = useState("Normal");
  const [detections, setDetections] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const voiceUnlocked = useRef(false);
  const lastSpoken = useRef("");
  const pendingSpeech = useRef(null);
  const latestDetections = useRef([]);
  const announcementTimer = useRef(null);
  const lastLanguage = useRef("English");

  const cancelSpeech = () => {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();
    pendingSpeech.current = null;

    if (announcementTimer.current) {
      clearTimeout(announcementTimer.current);
      announcementTimer.current = null;
    }
  };

  const getLabel = (item) => {
    const raw =
      item.label ??
      item.class_name ??
      item.name ??
      item.class ??
      item.object ??
      item.category ??
      item.type;

    if (typeof raw === "number") {
      return `Object ${raw}`;
    }

    if (typeof raw === "string" && raw.trim()) {
      return raw.trim().replace(/_/g, " ");
    }

    return "Obstacle";
  };

  const getHindiLabel = (label) => {
    const key = label.toLowerCase().replace(/\s+/g, "_");
    return HINDI_LABELS[key] || label;
  };

  const getDistanceCm = (item) => {
    const cm = Number(item.distance_cm);

    if (
      item.distance_cm !== undefined &&
      item.distance_cm !== null &&
      Number.isFinite(cm) &&
      cm > 0
    ) {
      return cm;
    }

    const rawDistance = item.dist ?? item.distance;

    if (
      rawDistance !== undefined &&
      rawDistance !== null &&
      Number.isFinite(Number(rawDistance)) &&
      Number(rawDistance) > 0
    ) {
      // Existing backend fallback: dist/distance is assumed to be metres.
      return Number(rawDistance) * 100;
    }

    return Infinity;
  };

  const getRisk = (item) => {
    const cm = getDistanceCm(item);

    if (!Number.isFinite(cm)) return "Unknown";
    if (cm <= 100) return "High";
    if (cm <= 250) return "Moderate";
    return "Low";
  };

  const getZone = (item) =>
    String(item.zone || item.direction || item.position || "ahead");

  const getHindiDirection = (zone) => {
    const key = String(zone).toLowerCase().replace(/_/g, "-");
    return HINDI_DIRECTIONS[key] || "आपके आसपास";
  };

  const formatDistance = (item) => {
    if (!item) return "—";

    const cm = getDistanceCm(item);
    return Number.isFinite(cm) ? `${(cm / 100).toFixed(1)} m` : "—";
  };

  const getIcon = (label) => {
    const name = (label || "").toLowerCase();

    if (name.includes("person")) return Eye;
    if (name.includes("chair")) return Footprints;
    return AlertTriangle;
  };

  const getDirection = (zone) => {
    if (!zone) return "Direction unavailable";

    return zone
      .toLowerCase()
      .replace(/_/g, " ")
      .replace(/-/g, " ");
  };


  const nearest = detections.length
    ? [...detections].sort(
        (a, b) => getDistanceCm(a) - getDistanceCm(b)
      )[0]
    : null;

  // Speak one complete announcement at a time.
  

  // Speak announcements one at a time without interrupting the current sentence.
  const speak = (message, selectedLanguage = language) => {
    if (!("speechSynthesis" in window) || !message) return;

    const synth = window.speechSynthesis;

    const createUtterance = (text, lang) => {
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = synth.getVoices();

      if (lang === "Hindi") {
        const hindiVoice =
          voices.find(v => v.lang.toLowerCase() === "hi-in") ||
          voices.find(v => v.lang.toLowerCase().startsWith("hi"));

        utterance.lang = "hi-IN";
        if (hindiVoice) {
          utterance.voice = hindiVoice;
          utterance.lang = hindiVoice.lang;
        }
      } else {
        const englishVoice =
          voices.find(v => v.lang.toLowerCase() === "en-in") ||
          voices.find(v => v.lang.toLowerCase().startsWith("en"));

        utterance.lang = "en-IN";
        if (englishVoice) {
          utterance.voice = englishVoice;
          utterance.lang = englishVoice.lang;
        }
      }

      utterance.rate =
        intensity === "High" ? 1.15 :
        intensity === "Low" ? 0.85 : 1;

      utterance.pitch = 1;
      utterance.volume = 1;
      return utterance;
    };

    const playNextPending = () => {
      const next = pendingSpeech.current;
      pendingSpeech.current = null;

      if (!next) return;

      const nextUtterance = createUtterance(
        next.message,
        next.language
      );

      nextUtterance.onend = playNextPending;
      nextUtterance.onerror = playNextPending;

      synth.resume();
      synth.speak(nextUtterance);
    };

    if (synth.speaking || synth.pending) {
      pendingSpeech.current = {
        message,
        language: selectedLanguage
      };
      return;
    }

    const utterance = createUtterance(message, selectedLanguage);
    utterance.onend = playNextPending;
    utterance.onerror = playNextPending;

    synth.resume();
    synth.speak(utterance);
  };



  // Fetch backend status.
  useEffect(() => {
    let active = true;

    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API}/api/status`);
        if (!response.ok) throw new Error("Backend unavailable");

        const data = await response.json();
        if (!active) return;

        setRunning(Boolean(data.running));

        const incoming = Array.isArray(data.detections)
          ? data.detections
          : [];

        latestDetections.current = incoming;
        setDetections(incoming);
        setError(data.error || null);
      } catch {
        if (!active) return;
        setError("Cannot connect to detection backend");
        setRunning(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  // Start / stop assistance.
  const toggleAssistance = async () => {
    setLoading(true);
    setError(null);

    if (!running) {
      voiceUnlocked.current = true;
      lastSpoken.current = "";
      cancelSpeech();

      speak(
        language === "Hindi"
          ? "ब्लाइंड असिस्ट शुरू हो गया है। आगे बढ़ने से पहले आसपास ध्यान दें।"
          : "Blind Assist started. Please stay alert to your surroundings."
      );
    } else {
      voiceUnlocked.current = false;
      lastSpoken.current = "";
      cancelSpeech();
    }

    try {
      const endpoint = running ? "/api/stop" : "/api/start";
      const response = await fetch(`${API}${endpoint}`, {
        method: "POST"
      });

      if (!response.ok) throw new Error("Could not control assistance");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Immediately cancel the old language when the user switches language.
  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
    lastLanguage.current = newLanguage;
    lastSpoken.current = "";
    cancelSpeech();

    // Announce the current surroundings in the newly selected language.
    if (running && voiceUnlocked.current) {
      announcementTimer.current = setTimeout(() => {
        const current = latestDetections.current;

        if (!current || current.length === 0) {
          speak(
            newLanguage === "Hindi"
              ? "आवाज़ हिंदी में बदल दी गई है। अभी कोई वस्तु दिखाई नहीं दे रही है।"
              : "Voice changed to English. No objects are currently detected.",
            newLanguage
          );
          return;
        }

        announceObjects(current, newLanguage);
      }, 250);
    }
  };

  // Create a single announcement from the current objects.
  const announceObjects = (items, selectedLanguage = language) => {
    if (!items || items.length === 0) return;

    // Keep only one detection per object class and direction.
    const uniqueMap = new Map();

    items.forEach(item => {
      const label = getLabel(item);
      const zone = getZone(item);
      const key = `${label.toLowerCase()}-${zone.toLowerCase()}`;
      const existing = uniqueMap.get(key);

      // Retain the closer instance of the same class/direction.
      if (!existing || getDistanceCm(item) < getDistanceCm(existing)) {
        uniqueMap.set(key, item);
      }
    });

    const unique = Array.from(uniqueMap.values()).sort(
      (a, b) => getDistanceCm(a) - getDistanceCm(b)
    );

    if (unique.length === 0) return;

    const descriptions = unique.map((item, index) => {
      const label = getLabel(item);
      const zone = getZone(item);
      const cm = getDistanceCm(item);
      const risk = getRisk(item);

      const distanceText = Number.isFinite(cm)
        ? `${(cm / 100).toFixed(1)} ${selectedLanguage === "Hindi" ? "मीटर" : "metres"}`
        : "";

      if (selectedLanguage === "Hindi") {
        const hindiLabel = getHindiLabel(label);
        const hindiZone = getHindiDirection(zone);

        const warning =
          risk === "High"
            ? "बहुत पास है। रुक जाइए।"
            : risk === "Moderate"
              ? "सावधान। धीरे चलें।"
              : "सावधानी से आगे बढ़ें।";

        return `${index + 1}. ${hindiLabel}, ${hindiZone}${distanceText ? `, ${distanceText}` : ""}। ${warning}`;
      }

      const warning =
        risk === "High"
          ? "Very close. Stop."
          : risk === "Moderate"
            ? "Caution. Move slowly."
            : "Proceed carefully.";

      return `${index + 1}. ${label}, ${getDirection(zone)}${distanceText ? `, ${distanceText}` : ""}. ${warning}`;
    });

    const message =
      selectedLanguage === "Hindi"
        ? `ध्यान दें। ${unique.length} वस्तुएँ दिखाई दे रही हैं। ${descriptions.join(" अगली वस्तु। ")}`
        : `Attention. ${unique.length} objects detected. ${descriptions.join(". Next obstacle. ")}`;

    speak(message, selectedLanguage);
  };

  // Announce only when the set of objects changes.
  useEffect(() => {
    if (!running || !voiceUnlocked.current || detections.length === 0) {
      if (announcementTimer.current) {
        clearTimeout(announcementTimer.current);
        announcementTimer.current = null;
      }
      return;
    }

    const normalized = detections.map(item => ({
      label: getLabel(item),
      zone: getZone(item)
    }));

    const signature = Array.from(
      new Set(normalized.map(
        object => `${object.label.toLowerCase()}-${object.zone.toLowerCase()}`
      ))
    ).sort().join("|");

    if (!signature || signature === lastSpoken.current) return;

    if (announcementTimer.current) {
      clearTimeout(announcementTimer.current);
    }

    // Small debounce so rapid frame changes don't trigger speech repeatedly.
    announcementTimer.current = setTimeout(() => {
      if (!running || !voiceUnlocked.current) return;
      
      console.log("Hindi announcement triggered:", signature, language);
      lastSpoken.current = signature;
      announceObjects(latestDetections.current, language);
    }, 1000);

    return () => {
      if (announcementTimer.current) {
        clearTimeout(announcementTimer.current);
      }
    };
  }, [running, detections, language, intensity]);

  // Clear voice state when assistance stops.
  useEffect(() => {
    if (!running) {
      lastSpoken.current = "";
      cancelSpeech();
    }
  }, [running]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Eye size={25} /></div>
          <div>
            <h1>Blind<span>Assist</span></h1>
            <p>VISION • GUIDANCE • SAFETY</p>
          </div>
        </div>

        <div className="side-label">YOUR ASSISTANCE</div>
        <div className="nav-item active">
          <Activity size={18}/> Live Dashboard
        </div>

        <div className="side-label settings-label">PREFERENCES</div>

        <div className="setting-block">
          <label><Languages size={15}/> Voice language</label>
          <select value={language} onChange={e => handleLanguageChange(e.target.value)}>
            <option>English</option>
            <option>Hindi</option>
          </select>
        </div>

        <div className="setting-block">
          <label><Waves size={15}/> Alert intensity</label>
          <select value={intensity} onChange={e => setIntensity(e.target.value)}>
            <option>Low</option>
            <option>Normal</option>
            <option>High</option>
          </select>
        </div>

        <div className="sidebar-bottom">
          <div className="safe-icon"><Shield size={18}/></div>
          <strong>Your safety, our priority.</strong>
          <p>Designed to support your awareness of the surroundings—not replace your white cane.</p>
          <div className="version">BLINDASSIST <span>•</span> PROTOTYPE 1.0</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">ASSISTIVE VISION SYSTEM</div>
            <h2>Live Dashboard</h2>
            <p className="welcome-text">Stay aware of what's around you.</p>
          </div>

          <div className={`status-pill ${running ? "online" : "offline"}`}>
            <span className="status-dot"/>
            {running ? "System Online" : "System Paused"}
          </div>
        </header>

        <section className="overview">
          <div className="metric-card">
            <div className="metric-icon cyan"><Scan size={19}/></div>
            <div>
              <span className="metric-label">Detection Engine</span>
              <strong>{running ? "Active" : "Paused"}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon blue"><Radio size={19}/></div>
            <div>
              <span className="metric-label">Objects Detected</span>
              <strong>{running ? String(detections.length).padStart(2, "0") : "—"}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon violet"><Navigation size={19}/></div>
            <div>
              <span className="metric-label">Nearest Obstacle</span>
              <strong>{running ? formatDistance(nearest) : "—"}</strong>
            </div>
          </div>
        </section>

        <section className="dashboard-grid">
          <div className="camera-card">
            <div className="card-header">
              <div><Camera size={18}/><h3>Live Environment</h3></div>
              <span className="live-tag">
                <span className="status-dot"/> {running ? "LIVE" : "OFFLINE"}
              </span>
            </div>

            <div className="camera-view">
              {running ? (
                <img
                  src={`${API}/api/video`}
                  alt="Live camera detection feed"
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain"
                  }}
                />
              ) : (
                <div className="camera-placeholder">
                  <div className="camera-circle"><Camera size={34}/></div>
                  <h3>Camera Feed</h3>
                  <p>Start assistance to view the live camera feed.</p>
                  <div className="camera-demo-label">
                    <CircleDot size={12}/> CAMERA PREVIEW
                  </div>
                </div>
              )}
            </div>

            <div className="camera-footer">
              <span><CircleDot size={13}/> Camera source</span>
              <span>{running ? "Connected" : "Awaiting connection"}</span>
            </div>
          </div>

          <div className="right-column">
            <div className="system-card">
              <div className="card-header">
                <div><Activity size={18}/><h3>System Monitor</h3></div>
              </div>

              <div className={`system-banner ${running ? "" : "paused"}`}>
                <span className="status-dot"/>
                {error || (running
                  ? "Detection system is running"
                  : "Detection system paused")}
              </div>

              <div className="system-details">
                <div><span>Engine</span><strong>YOLOv8</strong></div>
                <div><span>Voice</span><strong>{language}</strong></div>
                <div><span>Alert Mode</span><strong>{intensity}</strong></div>
              </div>
            </div>

            <div className="alert-card">
              <div className="card-header">
                <div><Volume2 size={18}/><h3>Latest Voice Alert</h3></div>
              </div>

              <div className="alert-message">
                <div className="alert-wave"><Volume2 size={18}/></div>
                <div>
                  <strong>
                    {nearest
                      ? `${getLabel(nearest)} detected nearby`
                      : running
                        ? "No obstacles detected"
                        : "System paused"}
                  </strong>
                  <p>
                    {nearest
                      ? `${getLabel(nearest)} detected at ${formatDistance(nearest)}.`
                      : running
                        ? "Monitoring your surroundings."
                        : "Resume assistance to continue monitoring."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="detections-card">
          <div className="card-header detection-heading">
            <div><Scan size={18}/><h3>Detection Summary</h3></div>
            <span className="count-label">
              {running ? `${detections.length} OBJECTS` : "PAUSED"}
            </span>
          </div>

          <div className="detection-list">
            {detections.length > 0 ? (
              detections.map((item, index) => {
                const Icon = getIcon(getLabel(item));
                const risk = getRisk(item);

                return (
                  <div className="detection-row" key={item.id ?? `${getLabel(item)}-${index}`}>
                    <div className="object-icon"><Icon size={18}/></div>
                    <div className="object-info">
                      <strong>{getLabel(item)}</strong>
                      <span>{getDirection(getZone(item))}</span>
                    </div>
                    <div className="object-distance">
                      <strong>{formatDistance(item)}</strong>
                      <span>Distance</span>
                    </div>
                    <div className={`risk ${risk.toLowerCase()}`}>
                      {risk === "Unknown" ? "Unknown" : risk}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="camera-placeholder">
                <Scan size={25}/>
                <p>{running
                  ? "No objects detected yet. Keep the camera pointed at your surroundings."
                  : "Start assistance to see detected objects."}</p>
              </div>
            )}
          </div>

          <div className="demo-note">
            Live data from the detection backend • No sample detections
          </div>
        </section>

        <footer className="bottom-bar">
          <div>
            <Shield size={15}/>
            BlindAssist is designed to supplement—not replace—a traditional white cane.
          </div>

          <button
            className={`control-btn ${running ? "stop" : "start"}`}
            onClick={toggleAssistance}
            disabled={loading}
          >
            {running ? <Pause size={16}/> : <Play size={16}/>}
            {loading
              ? "Please wait..."
              : running
                ? "Pause Assistance"
                : "Start Assistance"}
          </button>
        </footer>
      </main>
    </div>
  );
}
