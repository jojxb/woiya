import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Configure axios
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
axios.defaults.baseURL = API_BASE_URL;

const App = () => {
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('home');
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [walletInfo, setWalletInfo] = useState(null);

  // Auth functions
  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const token = response.data.token;
      localStorage.setItem('woiya_token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(response.data.user);
      await fetchUserStats();
      setCurrentPage('dashboard');
    } catch (error) {
      alert('Login failed: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post('/api/auth/register', userData);
      const token = response.data.token;
      localStorage.setItem('woiya_token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(response.data.user);
      await fetchUserStats();
      setCurrentPage('dashboard');
    } catch (error) {
      alert('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const logout = () => {
    localStorage.removeItem('woiya_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setCurrentPage('home');
  };

  // Data fetching functions
  const fetchUserStats = async () => {
    try {
      const response = await axios.get('/api/dashboard/stats');
      setUserStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchJobs = async (category = null) => {
    try {
      let url = '/api/jobs';
      if (category) url += `?category=${category}`;
      const response = await axios.get(url);
      setJobs(response.data.jobs);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  const fetchWalletInfo = async () => {
    try {
      const response = await axios.get('/api/wallet');
      setWalletInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch wallet info:', error);
    }
  };

  // Initialize app
  useEffect(() => {
    const token = localStorage.getItem('woiya_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      axios.get('/api/user/profile')
        .then(response => {
          setUser(response.data);
          fetchUserStats();
          setCurrentPage('dashboard');
        })
        .catch(() => {
          localStorage.removeItem('woiya_token');
          delete axios.defaults.headers.common['Authorization'];
        });
    }
  }, []);

  // Components
  const Header = () => (
    <header className="app-header">
      <div className="header-container">
        <div className="logo">
          <h1>WOIYA</h1>
          <span>Marketplace Jasa Terpercaya</span>
        </div>
        <nav className="main-nav">
          <button 
            onClick={() => setCurrentPage('home')} 
            className={currentPage === 'home' ? 'active' : ''}
          >
            Beranda
          </button>
          {user && (
            <>
              <button 
                onClick={() => setCurrentPage('dashboard')} 
                className={currentPage === 'dashboard' ? 'active' : ''}
              >
                Dashboard
              </button>
              <button 
                onClick={() => setCurrentPage('jobs')} 
                className={currentPage === 'jobs' ? 'active' : ''}
              >
                {user.role === 'pencari_jasa' ? 'Pekerjaan Saya' : 'Cari Pekerjaan'}
              </button>
              <button 
                onClick={() => setCurrentPage('wallet')} 
                className={currentPage === 'wallet' ? 'active' : ''}
              >
                Dompet Digital
              </button>
            </>
          )}
        </nav>
        <div className="header-actions">
          {user ? (
            <div className="user-menu">
              <span className="user-greeting">Halo, {user.full_name}</span>
              <span className="user-balance">Rp {user.wallet_balance?.toLocaleString() || 0}</span>
              <button onClick={logout} className="logout-btn">Keluar</button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button onClick={() => setCurrentPage('login')} className="login-btn">Masuk</button>
              <button onClick={() => setCurrentPage('register')} className="register-btn">Daftar</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );

  const HomePage = () => (
    <div className="home-page">
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <h1>Temukan Jasa Terpercaya dengan Sistem Bidding Transparan</h1>
            <p>WOIYA menghubungkan pencari jasa dengan penyedia jasa terbaik melalui sistem lelang yang adil dan transparan</p>
            <div className="hero-features">
              <div className="feature">
                <div className="feature-icon">💰</div>
                <h3>Sistem Bidding</h3>
                <p>Bandingkan tawaran dari berbagai penyedia jasa</p>
              </div>
              <div className="feature">
                <div className="feature-icon">🔒</div>
                <h3>Escrow Payment</h3>
                <p>Dana aman sampai pekerjaan selesai</p>
              </div>
              <div className="feature">
                <div className="feature-icon">⭐</div>
                <h3>Rating & Ulasan</h3>
                <p>Sistem rating transparan dari pengguna</p>
              </div>
            </div>
            <button 
              onClick={() => setCurrentPage('register')} 
              className="hero-cta"
            >
              Mulai Sekarang
            </button>
          </div>
        </div>
      </section>

      <section className="categories-section">
        <div className="container">
          <h2>Kategori Layanan</h2>
          <div className="categories-grid">
            <div className="category-card">
              <div className="category-icon">📦</div>
              <h3>Kurir & Logistik</h3>
              <p>Antar barang, pindahan, belanja</p>
            </div>
            <div className="category-card">
              <div className="category-icon">🔧</div>
              <h3>Perbaikan Rumah</h3>
              <p>Listrik, ledeng, AC, bangunan</p>
            </div>
            <div className="category-card">
              <div className="category-icon">🏠</div>
              <h3>Asisten Harian</h3>
              <p>Kebersihan, dapur, cuci kendaraan</p>
            </div>
            <div className="category-card">
              <div className="category-icon">🐕</div>
              <h3>Perawatan Hewan</h3>
              <p>Urus kucing, urus anjing</p>
            </div>
            <div className="category-card">
              <div className="category-icon">📚</div>
              <h3>Edukasi & Belajar</h3>
              <p>Les privat, asisten pengajar</p>
            </div>
            <div className="category-card">
              <div className="category-icon">🎨</div>
              <h3>Acara & Kreatif</h3>
              <p>Bantuan acara, fotografi</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );

  const LoginPage = () => {
    const [formData, setFormData] = useState({ email: '', password: '' });

    const handleSubmit = (e) => {
      e.preventDefault();
      login(formData.email, formData.password);
    };

    return (
      <div className="auth-page">
        <div className="auth-container">
          <div className="auth-card">
            <h2>Masuk ke WOIYA</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />
              </div>
              <button type="submit" className="auth-submit">Masuk</button>
            </form>
            <p className="auth-switch">
              Belum punya akun? 
              <button onClick={() => setCurrentPage('register')}>Daftar di sini</button>
            </p>
          </div>
        </div>
      </div>
    );
  };

  const RegisterPage = () => {
    const [formData, setFormData] = useState({
      email: '',
      password: '',
      full_name: '',
      phone: '',
      role: 'pencari_jasa'
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      register(formData);
    };

    return (
      <div className="auth-page">
        <div className="auth-container">
          <div className="auth-card">
            <h2>Daftar ke WOIYA</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nama Lengkap</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>No. Telepon</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Saya ingin menjadi</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                >
                  <option value="pencari_jasa">Pencari Jasa</option>
                  <option value="penyedia_jasa">Penyedia Jasa</option>
                </select>
              </div>
              <button type="submit" className="auth-submit">Daftar</button>
            </form>
            <p className="auth-switch">
              Sudah punya akun? 
              <button onClick={() => setCurrentPage('login')}>Masuk di sini</button>
            </p>
          </div>
        </div>
      </div>
    );
  };

  const Dashboard = () => {
    useEffect(() => {
      if (user) {
        fetchUserStats();
      }
    }, [user]);

    if (!userStats) return <div className="loading">Loading...</div>;

    return (
      <div className="dashboard">
        <div className="container">
          <h2>Dashboard {user.role === 'pencari_jasa' ? 'Pencari Jasa' : 'Penyedia Jasa'}</h2>
          
          <div className="stats-grid">
            {user.role === 'pencari_jasa' ? (
              <>
                <div className="stat-card">
                  <h3>Total Pekerjaan</h3>
                  <div className="stat-number">{userStats.total_jobs}</div>
                </div>
                <div className="stat-card">
                  <h3>Pekerjaan Aktif</h3>
                  <div className="stat-number">{userStats.active_jobs}</div>
                </div>
                <div className="stat-card">
                  <h3>Pekerjaan Selesai</h3>
                  <div className="stat-number">{userStats.completed_jobs}</div>
                </div>
                <div className="stat-card">
                  <h3>Saldo Dompet</h3>
                  <div className="stat-number">Rp {userStats.wallet_balance?.toLocaleString()}</div>
                </div>
              </>
            ) : (
              <>
                <div className="stat-card">
                  <h3>Total Penawaran</h3>
                  <div className="stat-number">{userStats.total_bids}</div>
                </div>
                <div className="stat-card">
                  <h3>Penawaran Diterima</h3>
                  <div className="stat-number">{userStats.selected_bids}</div>
                </div>
                <div className="stat-card">
                  <h3>Total Penghasilan</h3>
                  <div className="stat-number">Rp {userStats.total_earnings?.toLocaleString()}</div>
                </div>
                <div className="stat-card">
                  <h3>Rating</h3>
                  <div className="stat-number">⭐ {userStats.rating}</div>
                </div>
              </>
            )}
          </div>

          <div className="dashboard-actions">
            {user.role === 'pencari_jasa' ? (
              <button 
                onClick={() => setCurrentPage('create-job')} 
                className="primary-btn"
              >
                Buat Pekerjaan Baru
              </button>
            ) : (
              <button 
                onClick={() => setCurrentPage('jobs')} 
                className="primary-btn"
              >
                Cari Pekerjaan
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  const JobsPage = () => {
    useEffect(() => {
      fetchJobs();
    }, []);

    const placeBid = async (jobId) => {
      const amount = prompt('Masukkan nominal penawaran (Rp):');
      const message = prompt('Pesan untuk pemberi kerja:');
      const completion_time = prompt('Estimasi waktu penyelesaian (contoh: 2 hari):');

      if (amount && message && completion_time) {
        try {
          await axios.post(`/api/jobs/${jobId}/bids`, {
            job_id: jobId,
            amount: parseInt(amount),
            message: message,
            completion_time: completion_time
          });
          alert('Penawaran berhasil dikirim!');
          fetchJobs(); // Refresh jobs
        } catch (error) {
          alert('Gagal mengirim penawaran: ' + (error.response?.data?.detail || 'Unknown error'));
        }
      }
    };

    const viewJobDetails = async (jobId) => {
      try {
        const response = await axios.get(`/api/jobs/${jobId}`);
        setSelectedJob(response.data.job);
        setCurrentPage('job-details');
      } catch (error) {
        alert('Gagal mengambil detail pekerjaan');
      }
    };

    return (
      <div className="jobs-page">
        <div className="container">
          <div className="page-header">
            <h2>{user?.role === 'pencari_jasa' ? 'Pekerjaan Saya' : 'Pekerjaan Tersedia'}</h2>
            {user?.role === 'pencari_jasa' && (
              <button onClick={() => setCurrentPage('create-job')} className="primary-btn">
                Buat Pekerjaan Baru
              </button>
            )}
          </div>

          <div className="jobs-grid">
            {jobs.map(job => (
              <div key={job.id} className="job-card">
                <div className="job-header">
                  <h3>{job.title}</h3>
                  <span className={`job-status ${job.status}`}>{job.status}</span>
                </div>
                <p className="job-description">{job.description}</p>
                <div className="job-details">
                  <div className="job-budget">
                    Rp {job.budget_min?.toLocaleString()} - Rp {job.budget_max?.toLocaleString()}
                  </div>
                  <div className="job-meta">
                    <span className="job-category">{job.category}</span>
                    <span className="job-bids">{job.bids_count} penawaran</span>
                  </div>
                </div>
                <div className="job-actions">
                  <button onClick={() => viewJobDetails(job.id)} className="secondary-btn">
                    Lihat Detail
                  </button>
                  {user?.role === 'penyedia_jasa' && job.status === 'open' && (
                    <button onClick={() => placeBid(job.id)} className="primary-btn">
                      Buat Penawaran
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {jobs.length === 0 && (
            <div className="empty-state">
              <p>Tidak ada pekerjaan yang tersedia</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const CreateJobPage = () => {
    const [formData, setFormData] = useState({
      title: '',
      description: '',
      category: 'courier_logistik',
      budget_min: '',
      budget_max: '',
      address: '',
      deadline: '',
      requirements: ['']
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const jobData = {
          ...formData,
          budget_min: parseInt(formData.budget_min),
          budget_max: parseInt(formData.budget_max),
          location: { lat: -6.2088, lng: 106.8456 }, // Default Jakarta
          deadline: new Date(formData.deadline).toISOString(),
          requirements: formData.requirements.filter(req => req.trim())
        };

        await axios.post('/api/jobs', jobData);
        alert('Pekerjaan berhasil dibuat!');
        setCurrentPage('jobs');
      } catch (error) {
        alert('Gagal membuat pekerjaan: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="create-job-page">
        <div className="container">
          <h2>Buat Pekerjaan Baru</h2>
          <form onSubmit={handleSubmit} className="job-form">
            <div className="form-group">
              <label>Judul Pekerjaan</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label>Deskripsi</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label>Kategori</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
              >
                <option value="courier_logistik">Kurir & Logistik</option>
                <option value="perbaikan_rumah">Perbaikan Rumah</option>
                <option value="asisten_harian">Asisten Harian</option>
                <option value="perawatan_hewan">Perawatan Hewan</option>
                <option value="edukasi_belajar">Edukasi & Belajar</option>
                <option value="acara_kreatif">Acara & Kreatif</option>
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Budget Minimum (Rp)</label>
                <input
                  type="number"
                  value={formData.budget_min}
                  onChange={(e) => setFormData({...formData, budget_min: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Budget Maksimum (Rp)</label>
                <input
                  type="number"
                  value={formData.budget_max}
                  onChange={(e) => setFormData({...formData, budget_max: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Alamat</label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                required
              />
            </div>

            <div className="form-group">
              <label>Deadline</label>
              <input
                type="datetime-local"
                value={formData.deadline}
                onChange={(e) => setFormData({...formData, deadline: e.target.value})}
                required
              />
            </div>

            <button type="submit" className="primary-btn">Buat Pekerjaan</button>
          </form>
        </div>
      </div>
    );
  };

  const WalletPage = () => {
    useEffect(() => {
      fetchWalletInfo();
    }, []);

    const makePayment = (paymentMethod) => {
      alert(`Redirecting to ${paymentMethod} payment gateway...`);
    };

    if (!walletInfo) return <div className="loading">Loading...</div>;

    return (
      <div className="wallet-page">
        <div className="container">
          <h2>Dompet Digital</h2>
          
          <div className="wallet-balance">
            <h3>Saldo Saat Ini</h3>
            <div className="balance-amount">Rp {walletInfo.balance?.toLocaleString()}</div>
          </div>

          <div className="payment-methods">
            <h3>Metode Pembayaran</h3>
            <div className="payment-grid">
              <button onClick={() => makePayment('GoPay')} className="payment-method">
                <div className="payment-icon">💰</div>
                <span>GoPay</span>
              </button>
              <button onClick={() => makePayment('OVO')} className="payment-method">
                <div className="payment-icon">🟣</div>
                <span>OVO</span>
              </button>
              <button onClick={() => makePayment('Virtual Account')} className="payment-method">
                <div className="payment-icon">🏦</div>
                <span>Virtual Account</span>
              </button>
            </div>
          </div>

          <div className="transaction-history">
            <h3>Riwayat Transaksi</h3>
            <div className="transactions-list">
              {walletInfo.recent_transactions?.map(transaction => (
                <div key={transaction.id} className="transaction-item">
                  <div className="transaction-info">
                    <div className="transaction-type">
                      {transaction.payer_id === user?.id ? 'Pembayaran' : 'Penerimaan'}
                    </div>
                    <div className="transaction-status">{transaction.status}</div>
                  </div>
                  <div className="transaction-amount">
                    Rp {transaction.amount?.toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const JobDetailsPage = () => {
    const selectBid = async (bidId) => {
      try {
        await axios.post(`/api/jobs/${selectedJob.id}/select-bid/${bidId}`);
        alert('Penawaran berhasil dipilih!');
        // Refresh job details
        const response = await axios.get(`/api/jobs/${selectedJob.id}`);
        setSelectedJob(response.data.job);
      } catch (error) {
        alert('Gagal memilih penawaran: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    if (!selectedJob) return <div className="loading">Loading...</div>;

    return (
      <div className="job-details-page">
        <div className="container">
          <button onClick={() => setCurrentPage('jobs')} className="back-btn">
            ← Kembali
          </button>
          
          <div className="job-details">
            <h2>{selectedJob.title}</h2>
            <div className="job-meta">
              <span className="job-category">{selectedJob.category}</span>
              <span className={`job-status ${selectedJob.status}`}>{selectedJob.status}</span>
            </div>
            
            <div className="job-content">
              <p>{selectedJob.description}</p>
              <div className="job-info">
                <div><strong>Budget:</strong> Rp {selectedJob.budget_min?.toLocaleString()} - Rp {selectedJob.budget_max?.toLocaleString()}</div>
                <div><strong>Alamat:</strong> {selectedJob.address}</div>
                <div><strong>Deadline:</strong> {new Date(selectedJob.deadline).toLocaleDateString()}</div>
              </div>
            </div>

            <div className="bids-section">
              <h3>Penawaran ({selectedJob.bids?.length || 0})</h3>
              <div className="bids-list">
                {selectedJob.bids?.map(bid => (
                  <div key={bid.id} className={`bid-card ${bid.is_selected ? 'selected' : ''}`}>
                    <div className="bid-header">
                      <h4>{bid.bidder_name}</h4>
                      <div className="bid-rating">⭐ {bid.bidder_rating}</div>
                    </div>
                    <div className="bid-amount">Rp {bid.amount?.toLocaleString()}</div>
                    <div className="bid-time">{bid.completion_time}</div>
                    <p>{bid.message}</p>
                    {user?.id === selectedJob.creator_id && !selectedJob.selected_bid_id && selectedJob.status === 'open' && (
                      <button onClick={() => selectBid(bid.id)} className="select-bid-btn">
                        Pilih Penawaran
                      </button>
                    )}
                    {bid.is_selected && (
                      <span className="selected-badge">Terpilih</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Main render
  const renderPage = () => {
    switch(currentPage) {
      case 'home': return <HomePage />;
      case 'login': return <LoginPage />;
      case 'register': return <RegisterPage />;
      case 'dashboard': return <Dashboard />;
      case 'jobs': return <JobsPage />;
      case 'create-job': return <CreateJobPage />;
      case 'wallet': return <WalletPage />;
      case 'job-details': return <JobDetailsPage />;
      default: return <HomePage />;
    }
  };

  return (
    <div className="App">
      <Header />
      <main className="main-content">
        {renderPage()}
      </main>
      <footer className="app-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h4>WOIYA</h4>
              <p>Marketplace jasa terpercaya dengan sistem bidding transparan</p>
            </div>
            <div className="footer-section">
              <h4>Layanan</h4>
              <ul>
                <li>Kurir & Logistik</li>
                <li>Perbaikan Rumah</li>
                <li>Asisten Harian</li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Bantuan</h4>
              <ul>
                <li>Pusat Bantuan</li>
                <li>Kontak Kami</li>
                <li>Syarat & Ketentuan</li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2024 WOIYA. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;