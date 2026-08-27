import { Outlet, NavLink, useNavigate } from "react-router";
import { Hand, Menu, X } from "lucide-react";
import { useEffect,useState } from "react";//add
import { useLocation } from "react-router";//add
import { User, LogOut } from "lucide-react";//add



export default function Root() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinks = [
    { to: "/", label: "Home", exact: true },
    { to: "/translate", label: "Sign a Word" },
    { to: "/Detect", label: "Live Detection" },
    // { to: "/alphabet", label: "Fingerspelling" },
  ];

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium px-4 py-2 rounded-full transition-all ${
      isActive
        ? "bg-[#6C47FF] text-white shadow-sm"
        : "text-[#7B7BA0] hover:text-[#1A1535] hover:bg-[#EEF0FF]"
    }`;


  
  
  
  //add
  const location = useLocation();
  const [user, setUser] = useState<any>(null);
  useEffect(() => {
      const savedUser = sessionStorage.getItem("user");

      if (savedUser) {
          setUser(JSON.parse(savedUser));
      } else {
          setUser(null);
      }
  }, [location.pathname]);
  console.log(user);
  //
  const [profileOpen, setProfileOpen] = useState(false);
  const handleLogout = () => {

    sessionStorage.clear();

    setUser(null);

    setProfileOpen(false);

    navigate("/");

  };

  //






  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#F5F4FF", fontFamily: "Inter, sans-serif" }}>
      {/* ── Navbar ───────────────────────────────────────────────────────────── */}
      <nav
        className="w-full flex items-center justify-between px-8 py-4 sticky top-0 z-50"
        style={{ background: "rgba(245,244,255,0.85)", backdropFilter: "blur(16px)", borderBottom: "1px solid #E2E0F8" }}
      >
        {/* Logo */}
        <button
          className="flex items-center gap-3"
          onClick={() => navigate("/")}
        >
          <div
            className="flex items-center justify-center rounded-xl"
            style={{ width: 38, height: 38, background: "#6C47FF" }}
          >
            <Hand size={18} color="white" />
          </div>
          <span className="font-bold text-base" style={{ color: "#1A1535" }}>EchoSign</span>
        </button>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map(({ to, label, exact }) => (
            <NavLink key={to} to={to} end={exact} className={linkClass}>
              {label}
            </NavLink>
          ))}
        </div>

        {/* CTA  apres modification */}
        <div className="hidden md:flex items-center gap-3">

        {
        //user ? (

        //<div
        //className="px-5 py-2 rounded-full font-semibold text-sm"
        //style={{
        //  background:"#EEF0FF",
        //  color:"#6C47FF"
        //}}
        //>
        //Welcome, {user.first_name}
        //</div>
        // )
        // :
        user ? (

        <>
            <div className="relative">

                <button
                    onClick={() => setProfileOpen(v => !v)}
                    className="flex items-center gap-3 px-5 py-2 rounded-full"
                    style={{
                        background:"#EEF0FF",
                        color:"#6C47FF"
                    }}
                >
                    <span>Welcome, {user.first_name}</span>
                    <User size={18}/>
                </button>

                {profileOpen && (

                        <div
                        className="absolute right-0 mt-2 w-64 rounded-2xl shadow-lg p-4 z-50"
                        style={{
                        background:"white",
                        border:"1px solid #E2E0F8"
                        }}
                        >

                        <div className="mb-4">

                        <div className="font-semibold">
                        {user.first_name} {user.last_name}
                        </div>

                        <div
                        className="text-sm"
                        style={{color:"#7B7BA0"}}
                        >
                        {user.email}
                        </div>

                        </div>

                        <hr className="mb-3"/>

                        <button

                        className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-[#EEF0FF]"

                        onClick={handleLogout}

                        >

                        <LogOut size={16}/>

                        Log out

                        </button>

                        </div>

                        )}







            </div>
        </>

        ) : (


        <NavLink
          to="/signin"
          className="text-sm font-semibold px-5 py-2 rounded-full"
          style={{
            background:"#6C47FF",
            color:"white"
          }}
        >
        Sign In
        </NavLink>
        )
        }

        </div>






        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 rounded-xl"
          style={{ background: "#EEF0FF" }}
          onClick={() => setMenuOpen(m => !m)}
        >
          {menuOpen ? <X size={20} color="#6C47FF" /> : <Menu size={20} color="#6C47FF" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {menuOpen && (
        <div
          className="md:hidden px-6 pb-4 flex flex-col gap-2"
          style={{ background: "rgba(245,244,255,0.97)", borderBottom: "1px solid #E2E0F8" }}
        >
          {navLinks.map(({ to, label, exact }) => (
            <NavLink
              key={to} to={to} end={exact}
              className={linkClass}
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </NavLink>
          ))}


          {navLinks.map(({ to, label, exact }) => (
          <NavLink key={to} to={to} end={exact} className={linkClass}>
            {label}
          </NavLink>
        ))}



          <NavLink
            to="/signup"
            className="text-sm font-semibold px-5 py-2.5 rounded-full text-center mt-1"
            style={{ background: "#6C47FF", color: "white" }}
            onClick={() => setMenuOpen(false)}
          >
            Create Account
          </NavLink>
        </div>
      )}

      {/* ── Page content ─────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────────── */}
      <footer
        className="px-8 py-5 flex flex-wrap items-center justify-between gap-4 text-xs"
        style={{ borderTop: "1px solid #E2E0F8", color: "#C4B0FF" }}
      >
        <span>© 2026 EchoSign · Bridging communication through AI</span>
      </footer>
    </div>
  );
}
