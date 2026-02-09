import { useState, useEffect } from 'react';
import { getStores, createStore, deleteStore, getCurrentUser, logout } from './api';
import { ExternalLink, Trash2, RefreshCw, ShoppingBag, Lock, Plus, X, Copy, Check, LogOut, Database, HardDrive } from 'lucide-react';
import Login from './Login';
import './App.css';

const DEFAULT_PRODUCTS = [
  { name: "Classic T-Shirt", price: "20.00", description: "A classic cotton t-shirt" },
  { name: "Denim Jeans", price: "45.00", description: "Blue denim jeans" },
  { name: "Sneakers", price: "60.00", description: "Comfortable running shoes" }
];

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [adminPassword, setAdminPassword] = useState("");
  const [storageSize, setStorageSize] = useState(2);
  const [products, setProducts] = useState(DEFAULT_PRODUCTS);
  const [copied, setCopied] = useState(false);

  const loadUserProfile = async () => {
    try {
      const profile = await getCurrentUser();
      setUserProfile(profile);
      setIsAuthenticated(true);
    } catch (err) {
      console.error("Failed to load profile", err);
      setIsAuthenticated(false);
      localStorage.removeItem('token');
    }
  };

  const handleLogin = async () => {
    await loadUserProfile();
  };

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
    setUserProfile(null);
    setStores([]);
  };

  const fetchStores = async () => {
    setLoading(true);
    try {
      const data = await getStores();
      setStores(data);
      setError(null);
    } catch (err) {
      setError("Failed to fetch stores. Is the backend running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      loadUserProfile();
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchStores();
      const interval = setInterval(fetchStores, 10000); // Poll every 10s
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const generatePassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
    let pass = "";
    for (let i = 0; i < 16; i++) {
      pass += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setAdminPassword(pass);
  };

  const openModal = () => {
    generatePassword();
    setProducts(DEFAULT_PRODUCTS);
    setStorageSize(2);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(adminPassword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleProductChange = (index, field, value) => {
    const newProducts = [...products];
    newProducts[index][field] = value;
    setProducts(newProducts);
  };

  const addProductRow = () => {
    setProducts([...products, { name: "", price: "", description: "" }]);
  };

  const removeProductRow = (index) => {
    setProducts(products.filter((_, i) => i !== index));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    
    // Format products for backend
    const formattedProducts = products
      .filter(p => p.name && p.price)
      .map(p => `${p.name}|${p.price}|${p.description}`)
      .join('\n');

    try {
      await createStore({
        sample_products: formattedProducts,
        admin_password: adminPassword,
        storage_size_gi: storageSize
      });
      await fetchStores();
      await loadUserProfile(); // Refresh quota
      alert("Store creation started!");
      closeModal();
    } catch (err) {
      const msg = err.response?.data?.error || "Failed to create store. Quota exceeded?";
      setError(msg);
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this store?")) return;
    try {
      await deleteStore(id);
      setStores(stores.filter(s => s.id !== id));
      await loadUserProfile(); // Refresh quota
    } catch (err) {
      const msg = err.response?.data?.error || "Failed to delete store.";
      setError(msg);
      console.error(err);
    }
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="container">
      <header className="header">
        <div className="header-left">
          <h1><ShoppingBag className="icon" /> K8s WooCommerce Factory</h1>
          <p>Manage your Kubernetes-based stores</p>
        </div>
        {userProfile && (
          <div className="header-right">
            <div className="user-info">
              <div className="quota-badge">
                <Database size={16} />
                <span>{userProfile.current_stores || 0} / {userProfile.max_stores} Stores</span>
              </div>
              <div className="quota-badge">
                <HardDrive size={16} />
                <span>{userProfile.current_storage || 0} / {userProfile.max_storage} Gi</span>
              </div>
              <div className="user-name">{userProfile.username}</div>
              <button onClick={handleLogout} className="btn-icon" title="Logout">
                <LogOut size={18} />
              </button>
            </div>
          </div>
        )}
      </header>
      
      {error && <div className="error-banner">{error}</div>}

      <div className="main-content">
        <section className="list-section full-width">
          <div className="list-header">
            <h2>Your Stores</h2>
            <div className="actions">
              <button onClick={openModal} className="btn-primary">
                <Plus size={18} /> New Store
              </button>
              <button onClick={fetchStores} className="btn-icon" title="Refresh">
                <RefreshCw className={loading ? "spin icon" : "icon"} />
              </button>
            </div>
          </div>
          
          <div className="grid">
            {stores.length === 0 && !loading && <p className="empty-state">No stores provisioned yet.</p>}
            
            {stores.map(store => (
              <div key={store.id} className={`card ${store.status}`}>
                <div className="card-header">
                  <h3>Store: {store.id}</h3>
                  <span className={`badge ${store.status}`}>{store.status}</span>
                </div>

                <div className="card-body">
                   <div className="info-row">
                      <ExternalLink size={16} />
                      <a href={store.url} target="_blank" rel="noreferrer">{store.url}</a>
                   </div>
                   <div className="info-row">
                      <Lock size={16} />
                      <a href={`${store.url}/wp-admin`} target="_blank" rel="noreferrer">Admin Panel</a>
                   </div>

                   {store.owner && (
                     <div className="info-row">
                       <span className="label">Owner:</span> {store.owner}
                     </div>
                   )}

                   {store.storage_gi && (
                     <div className="info-row">
                       <HardDrive size={16} />
                       <span>{store.storage_gi} Gi Storage</span>
                     </div>
                   )}

                   <div className="credentials">
                     <h4>Credentials</h4>
                     <p>User: <code>admin</code></p>
                     <p>Pass: <code>{store.admin_password || "Check Secret"}</code></p>
                   </div>

                   <div className="notes">
                     <p><small>Note: Add <code>127.0.0.1 store-{store.id}.local</code> to /etc/hosts</small></p>
                   </div>
                </div>

                <div className="card-footer">
                  <button onClick={() => handleDelete(store.id)} className="btn-danger">
                    <Trash2 size={16} /> Delete Store
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>Launch New Store</h2>
              <button onClick={closeModal} className="btn-icon"><X size={20} /></button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {/* Admin Password Section */}
                <div className="form-group">
                  <label>Admin Password</label>
                  <div className="password-input-group">
                    <input
                      type="text"
                      value={adminPassword}
                      onChange={(e) => setAdminPassword(e.target.value)}
                      className="input-text"
                    />
                    <button type="button" onClick={generatePassword} className="btn-secondary" title="Regenerate">
                      <RefreshCw size={16} />
                    </button>
                    <button type="button" onClick={handleCopyPassword} className="btn-secondary" title="Copy">
                      {copied ? <Check size={16} /> : <Copy size={16} />}
                    </button>
                  </div>
                  <small className="help-text">This will be the password for the 'admin' user.</small>
                </div>

                {/* Storage Size Section */}
                <div className="form-group">
                  <label>WordPress Storage Size (Gi)</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={storageSize}
                    onChange={(e) => setStorageSize(parseInt(e.target.value))}
                    className="input-text"
                    required
                  />
                  <small className="help-text">Note: MySQL requires additional 2Gi. Total: {storageSize + 2}Gi</small>
                </div>

                {/* Products Section */}
                <div className="form-group">
                  <label>Initial Products</label>
                  <div className="products-list">
                    {products.map((product, index) => (
                      <div key={index} className="product-row">
                        <input 
                          type="text" 
                          placeholder="Product Name"
                          value={product.name}
                          onChange={(e) => handleProductChange(index, "name", e.target.value)}
                          className="input-text"
                          required
                        />
                        <input 
                          type="number" 
                          placeholder="Price"
                          value={product.price}
                          onChange={(e) => handleProductChange(index, "price", e.target.value)}
                          className="input-text price-input"
                          required
                        />
                        <input 
                          type="text" 
                          placeholder="Description"
                          value={product.description}
                          onChange={(e) => handleProductChange(index, "description", e.target.value)}
                          className="input-text desc-input"
                        />
                        <button type="button" onClick={() => removeProductRow(index)} className="btn-icon danger">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <button type="button" onClick={addProductRow} className="btn-secondary btn-sm">
                    <Plus size={14} /> Add Product
                  </button>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? <RefreshCw className="spin icon" /> : "Launch Store"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App
